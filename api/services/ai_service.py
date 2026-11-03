"""
Phase 31: AI explanation service.

Builds an explanation request from a REAL prediction record and forwards it
to the AI Assistant service (ai_assistant, port 8001). If the assistant is
unavailable, falls back to calling Ollama directly.
"""

import logging
import math
import time
from typing import Any

import httpx
import numpy as np
import pandas as pd

from api.config import (
    AI_ASSISTANT_BASE_URL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
)
from api.knowledge_base import classify_query, retrieve_knowledge

AI_SOURCE_ASSISTANT = "ai-assistant"
AI_SOURCE_OLLAMA = "ollama-direct"
AI_SOURCE_UNAVAILABLE = "unavailable"
AI_SOURCE_KNOWLEDGE = "knowledge-base"
AI_SOURCE_DEEPSEEK = "deepseek"
AI_SOURCE_TREE_SHAP = "xgboost-tree-shap"
logger = logging.getLogger(__name__)

# Prediction explanations should fail fast instead of leaving the user waiting
# for the general-purpose 5-minute Ollama timeout.
EXPLAIN_ASSISTANT_TIMEOUT_SECONDS = 8.0
EXPLAIN_OLLAMA_TIMEOUT_SECONDS = 35.0
EXPLAIN_MAX_PREDICTION_TOKENS = 160


class AIService:
    def __init__(self) -> None:
        # Assistant call: fail fast so we fall back to direct Ollama quickly.
        self.assistant_client = httpx.Client(timeout=20.0)
        # Direct Ollama with a long prompt on CPU can need > 90s.
        self.ollama_client = httpx.Client(timeout=300.0)

    def answer_general(self, question: str) -> dict[str, Any]:
        """
        Answer a general question (no prediction context).

        Routes to:
        - SYSTEM_KNOWLEDGE: retrieve docs + answer with LLM
        - DATA_QUERY: proxy to AI Assistant (Text-to-SQL)
        - HYBRID_QUERY: both
        - UNSUPPORTED_QUERY: explain limitations

        Returns dict with keys: answer, ai_available, source, sql_query (optional), results (optional).
        """
        query_type = classify_query(question)

        if query_type == "SYSTEM_KNOWLEDGE":
            return self._answer_knowledge(question)
        elif query_type == "DATA_QUERY":
            return self._answer_data(question)
        elif query_type == "HYBRID_QUERY":
            return self._answer_hybrid(question)
        else:
            return {
                "answer": (
                    "Cau hoi cua ban vuot qua pham vi du lieu va tai lieu hien co. "
                    "Toi co the ho tro: (1) Truy van thong ke du lieu gian lan tu Data Warehouse, "
                    "(2) Giai thich kien truc he thong, (3) Phan tich ket qua model XGBoost. "
                    "Vui long dat cau hoi cu the hon."
                ),
                "ai_available": True,
                "source": AI_SOURCE_KNOWLEDGE,
            }

    def _answer_knowledge(self, question: str) -> dict[str, Any]:
        """Answer a system knowledge question using doc retrieval + LLM."""
        kb = retrieve_knowledge(question)
        if not kb["found"]:
            return {
                "answer": (
                    "Toi chua co du lieu tai lieu de tra loi cau hoi nay. "
                    "Vui long hoi ve: kien truc he thong, bang du lieu, pipeline ETL, "
                    "model XGBoost, hoac API."
                ),
                "ai_available": True,
                "source": AI_SOURCE_KNOWLEDGE,
            }

        prompt = (
            f"Cau hoi: {question}\n\n"
            f"Tai lieu tham khao:\n{kb['context']}\n\n"
            "Tra loi bang tieng Viet dua tren tai lieu tren. "
            "Neu tai lieu khong du de tra loi, hay noi ro gioi han. "
            "Khong bia dat thong tin."
        )
        # Try AI Assistant first
        answer, source, sql_query, results = self._try_assistant(prompt)
        if answer is not None:
            result = {"answer": answer, "ai_available": True, "source": source, "sources": kb["sources"]}
            if sql_query:
                result["sql_query"] = sql_query
            if results:
                result["results"] = results
            return result
        # Fallback to Ollama
        answer, source = self._try_ollama(prompt)
        if answer is not None:
            return {"answer": answer, "ai_available": True, "source": source, "sources": kb["sources"]}
        return {
            "answer": "AI Assistant va Ollama khong hoat dong luc nay. Vui long thu lai sau.",
            "ai_available": False,
            "source": AI_SOURCE_UNAVAILABLE,
            "sources": kb["sources"],
        }

    def _answer_data(self, question: str) -> dict[str, Any]:
        """Answer a data query by proxying to AI Assistant (Text-to-SQL).

        IMPORTANT: Ollama direct is NOT used for quantitative data queries,
        because it would fabricate numbers. Only the AI Assistant (which
        generates + validates + executes real SQL) is authoritative.
        """
        answer, source, sql_query, results = self._try_assistant(question)
        if answer is not None:
            result: dict[str, Any] = {"answer": answer, "ai_available": True, "source": source}
            if sql_query:
                result["sql_query"] = sql_query
            if results:
                result["results"] = results
            return result
        return {
            "answer": (
                "Chuc nang truy van du lieu dang khong kha dung: AI Assistant "
                "(port 8001) khong phan hoi. He thong KHONG su dung Ollama de "
                "doan so lieu. Vui long kiem tra AI Assistant va thu lai."
            ),
            "ai_available": False,
            "source": AI_SOURCE_UNAVAILABLE,
        }

    def _answer_hybrid(self, question: str) -> dict[str, Any]:
        """Answer a hybrid query using both knowledge and data."""
        kb = retrieve_knowledge(question)
        data_result = self._answer_data(question)
        knowledge_answer = ""
        if kb["found"]:
            prompt = (
                f"Cau hoi: {question}\n\n"
                f"Tai lieu tham khao:\n{kb['context']}\n\n"
                "Tra loi bang tieng Viet dua tren tai lieu tren."
            )
            ans, src, _sql, _res = self._try_assistant(prompt)
            if ans is None:
                ans, src = self._try_ollama(prompt)
            if ans is not None:
                knowledge_answer = ans

        combined = ""
        if knowledge_answer:
            combined += knowledge_answer + "\n\n"
        if data_result.get("answer"):
            combined += "Ket qua truy van du lieu:\n" + data_result["answer"]

        if not combined.strip():
            combined = "Khong the tra loi cau hoi nay voi du lieu hien co."

        return {
            "answer": combined.strip(),
            "ai_available": data_result.get("ai_available", False) or bool(knowledge_answer),
            "source": data_result.get("source", AI_SOURCE_KNOWLEDGE),
            "sources": kb.get("sources", []),
        }
        prompt = question or (
            "Giai thich ket qua du doan gian luan nay theo nguyen vao du lieu thuc."
        )
        full_question = f"{prompt}\n\nDu lieu bau cua du doan (thuc):\n{context}"

        # Try AI Assistant service first (read-only Text-to-SQL capable).
        answer, source = self._try_assistant(full_question)
        if answer is not None:
            return {"answer": answer, "ai_available": True, "source": source}

        # Fallback: call Ollama directly on the host.
        answer, source = self._try_ollama(full_question)
        if answer is not None:
            return {"answer": answer, "ai_available": True, "source": source}

        return {
            "answer": (
                "AI Assistant va Ollama khong hoat dong luc nay. Du doan cua "
                "XGBoost van co hieu luc, nhung chua co giai thich tu AI. "
                "Vui long thu lai sau."
            ),
            "ai_available": False,
            "source": AI_SOURCE_UNAVAILABLE,
        }

    def explain(self, prediction_id: str, record: dict[str, Any], question: str | None = None) -> dict[str, Any]:
        """Explain a real prediction result using AI."""
        # TreeSHAP reads every feature used by this exact XGBoost prediction and
        # returns model-grounded attributions locally; it avoids waiting for an
        # LLM to interpret hundreds of mostly encoded columns.
        if record.get("input_mode") == "ieee-cis" and not (question and question.strip()):
            try:
                answer = self._explain_with_tree_shap(record)
                return {
                    "answer": answer,
                    "ai_available": True,
                    "source": AI_SOURCE_TREE_SHAP,
                }
            except Exception:
                logger.exception("TreeSHAP explanation failed for prediction %s", prediction_id)

        prompt = question or (
            "Giai thich ngan gon ket qua nay bang tieng Viet, toi da 3 y. "
            "Neu khong co SHAP thi khong ket luan dac trung nao la nguyen nhan."
        )
        # The prediction record may contain hundreds of raw columns. Sending all
        # of them to an LLM adds latency without providing feature attribution.
        context = self._build_context(record, max_features=18)
        full_question = f"{prompt}\n\nDu lieu thuc cua du doan:\n{context}"

        answer, source, sql_query, results = self._try_assistant(
            full_question, timeout=EXPLAIN_ASSISTANT_TIMEOUT_SECONDS
        )
        if answer is not None:
            result = {"answer": answer, "ai_available": True, "source": source}
            if sql_query:
                result["sql_query"] = sql_query
            if results:
                result["results"] = results
            return result

        answer, source = self._try_ollama(
            full_question,
            timeout=EXPLAIN_OLLAMA_TIMEOUT_SECONDS,
            options={"num_predict": EXPLAIN_MAX_PREDICTION_TOKENS, "temperature": 0.2},
        )
        if answer is not None:
            return {"answer": answer, "ai_available": True, "source": source}

        return {
            "answer": (
                "AI chưa phản hồi trong thời hạn chờ. Kết quả XGBoost vẫn hợp lệ; "
                "bạn có thể thử yêu cầu giải thích lại sau."
            ),
            "ai_available": False,
            "source": AI_SOURCE_UNAVAILABLE,
        }

    def _explain_with_tree_shap(self, record: dict[str, Any]) -> str:
        """Explain one IEEE-CIS prediction with native XGBoost TreeSHAP."""
        from xgboost import DMatrix

        from api.inference import get_inference_pipeline

        started = time.perf_counter()
        payload = record.get("input_payload") or {}
        if not isinstance(payload, dict):
            raise ValueError("Prediction input payload is not an object")

        pipeline = get_inference_pipeline()
        if not pipeline._loaded:
            pipeline.load()
        raw = pd.DataFrame([payload])
        for column in pipeline._get_expected_raw_columns():
            if column not in raw.columns:
                raw[column] = np.nan
        engineered = pipeline._engineer_features(raw)
        encoded = pipeline._encode_frequency(engineered)
        features = pipeline._preprocess(encoded)
        if features.shape[1] != len(pipeline.feature_cols):
            raise ValueError("Feature columns do not match the loaded XGBoost model")

        matrix = DMatrix(features, feature_names=list(pipeline.feature_cols))
        contributions = pipeline.model.get_booster().predict(
            matrix, pred_contribs=True, approx_contribs=False
        )[0]
        feature_contributions = contributions[:-1]
        base_margin = float(contributions[-1])
        margin = float(contributions.sum())
        model_probability = 1.0 / (1.0 + math.exp(-max(min(margin, 700), -700)))
        stored_probability = float(record["fraud_probability"])
        if not math.isclose(model_probability, stored_probability, rel_tol=1e-3, abs_tol=1e-3):
            raise ValueError(
                "TreeSHAP reconstruction differs from the stored model prediction"
            )

        def sigmoid(value: float) -> float:
            return 1.0 / (1.0 + math.exp(-max(min(value, 700), -700)))

        def display_value(value: Any) -> str:
            if value is None:
                return "thiếu"
            if isinstance(value, (float, np.floating)):
                if not np.isfinite(value):
                    return "thiếu"
                return f"{float(value):.5g}"
            return str(value)[:60]

        categorical_columns = pipeline.preprocessor.transformers[1][2]

        def feature_description(index: int) -> str:
            name = str(pipeline.feature_cols[index])
            encoded_value = float(features[0, index])
            if name.startswith("cat__"):
                for column in categorical_columns:
                    prefix = f"cat__{column}_"
                    if name.startswith(prefix):
                        category = name[len(prefix):]
                        active = "đang khớp" if encoded_value >= 0.5 else "không khớp"
                        original = payload.get(column)
                        original_text = (
                            f", giá trị đầu vào={display_value(original)}"
                            if original is not None else ""
                        )
                        return (
                            f"{column} thuộc nhóm {category} ({active}{original_text})"
                        )
                return f"{name} (giá trị mã hóa={display_value(encoded_value)})"

            if name.startswith("num__"):
                column = name[len("num__"):]
                if column.endswith("_freq"):
                    original_column = column[:-5]
                    original = payload.get(original_column)
                    return (
                        f"tần suất của {original_column}"
                        + (f" (đầu vào={display_value(original)})" if original is not None else "")
                    )
                if column.endswith("_missing"):
                    return f"cờ dữ liệu thiếu của {column[:-8]} (mã hóa={display_value(encoded_value)})"
                if column in payload:
                    return f"{column} (đầu vào={display_value(payload[column])})"
                if column in encoded.columns:
                    return f"{column} (giá trị sau biến đổi={display_value(encoded.iloc[0][column])})"
                return f"{column} (giá trị đã chuẩn hóa={display_value(encoded_value)})"
            return f"{name} (giá trị={display_value(encoded_value)})"

        def contribution_line(index: int, rank: int) -> str:
            value = float(feature_contributions[index])
            odds_factor = math.exp(max(min(value, 50), -50))
            return (
                f"{rank}. {feature_description(index)} — đóng góp {value:+.3f} log-odds "
                f"(tỷ lệ odds ×{odds_factor:.2f})"
            )

        positive = sorted(
            (i for i, value in enumerate(feature_contributions) if value > 0),
            key=lambda i: float(feature_contributions[i]), reverse=True,
        )[:8]
        negative = sorted(
            (i for i, value in enumerate(feature_contributions) if value < 0),
            key=lambda i: float(feature_contributions[i]),
        )[:8]

        predicted_label = int(record.get("is_fraud_predicted", stored_probability >= float(record.get("threshold", 0.5))))
        threshold = float(record.get("threshold", 0.5))
        lines = [
            "Giải thích XGBoost bằng TreeSHAP (phân tích toàn bộ "
            f"{len(feature_contributions):,} đặc trưng sau xử lý).",
            f"Kết quả: {'GIAN LẬN' if predicted_label else 'HỢP LỆ'}; "
            f"xác suất gian lận {stored_probability:.2%}, ngưỡng {threshold:.2%}.",
            f"Mốc nền của mô hình: {sigmoid(base_margin):.2%}; sau khi cộng đóng góp "
            f"của tất cả đặc trưng, xác suất là {model_probability:.2%}.",
            "",
            "Yếu tố đẩy điểm về phía gian lận (TreeSHAP dương):",
        ]
        lines.extend(
            [contribution_line(index, rank) for rank, index in enumerate(positive, 1)]
            or ["Không có đóng góp dương đáng kể."]
        )
        lines.extend(["", "Yếu tố kéo điểm ra xa gian lận (TreeSHAP âm):"])
        lines.extend(
            [contribution_line(index, rank) for rank, index in enumerate(negative, 1)]
            or ["Không có đóng góp âm đáng kể."]
        )
        lines.extend([
            "",
            "Cách đọc: TreeSHAP phân rã điểm log-odds của chính lần dự đoán này; "
            "đóng góp dương làm tăng và đóng góp âm làm giảm điểm gian lận. "
            "Đây là mức ảnh hưởng lên đầu ra mô hình, không khẳng định quan hệ nhân quả.",
            f"Thời gian tính giải thích cục bộ: {time.perf_counter() - started:.2f} giây.",
        ])
        return "\n".join(lines)
    def _build_context(
        self, record: dict[str, Any], *, max_features: int | None = None
    ) -> str:
        """Build a plain-text context from a real prediction record.

        When max_features is supplied, only compact, human-readable transaction
        fields are sent to the explanation model; no feature importance is implied.
        """
        lines = [
            f"- Ma du doan: {record.get('prediction_id')}",
            f"- Che do kiem thou: {record.get('input_mode')}",
            f"- Model: {record.get('model_version')} (XGBoost, thuc te)",
            f"- Nguong du doan: {record.get('threshold')}",
            f"- Xac suat gian lban (fraud_probability): {record.get('fraud_probability')}",
            f"- Nhan du doan: {'GIAN LUAN (1)' if record.get('is_fraud_predicted') == 1 else 'KHONG GIAN LUAN (0)'}",
            f"- Thoi gian thuc hien: {record.get('predicted_at')}",
            f"- Trang thai luu tru: {record.get('status')}",
            "",
            "Du lieu nhap vao (input_payload, luu tru trong lich su kiem thou):",
        ]
        payload = record.get("input_payload") or {}
        if isinstance(payload, dict) and payload:
            preferred = (
                "transaction_id", "transaction_dt", "transaction_amt", "product_cd",
                "card1", "card2", "card3", "card4", "card5", "card6",
                "addr1", "addr2", "dist1", "dist2", "p_emaildomain",
                "r_emaildomain", "device_type", "device_info",
            )
            if max_features is not None:
                selected = [key for key in preferred if key in payload and payload[key] is not None]
                selected.extend(
                    key for key, value in payload.items()
                    if key not in selected and value is not None
                )
                keys = selected[:max_features]
                lines.append("Mot so truong giao dich tham khao (khong phai giai thich SHAP):")
            else:
                keys = list(payload)
            for key in keys:
                value = payload[key]
                lines.append(f"  - {key}: {value}")
        else:
            lines.append("  (khong co)")
        lines.append("")
        lines.append(
            "Loi dan: Tra loi bang tieng Viet, chi su dung du lieu tren day. "
            "Khong bao gioc gat diem, nhan, hoac trinh thuoc tinh mo hinh. "
            "Phan biet rong rang: ket qua cua model XGBoost, giai thich cua AI, "
            "va du lieu thuc da truy van. Neu chua co by minh chung giai thich "
            "o cap feature (vd. SHAP), phai thong bao ro."
        )
        return "\n".join(lines)

    def _try_assistant(
        self, question: str, *, timeout: float | None = None
    ) -> tuple[str | None, str | None, str | None, list | None]:
        try:
            url = f"{AI_ASSISTANT_BASE_URL}/chat"
            request_options = {"timeout": timeout} if timeout is not None else {}
            response = self.assistant_client.post(
                url, json={"question": question}, **request_options
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer")
                if answer:
                    return answer, AI_SOURCE_ASSISTANT, data.get("sql_query"), data.get("results")
        except Exception:
            pass
        return None, None, None, None

    def _try_ollama(
        self,
        question: str,
        *,
        timeout: float | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[str | None, str | None]:
        try:
            url = f"{OLLAMA_BASE_URL}/api/chat"
            request_options = {"timeout": timeout} if timeout is not None else {}
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ban la tro chuyen AI ho tro phan tich gian lban giao dich thuong mai dien tu. Tra loi bang tieng Viet, chi du lieu duoc cung cap, khong bat giat so lieu.",
                    },
                    {"role": "user", "content": question},
                ],
                "stream": False,
            }
            if options:
                payload["options"] = options
            response = self.ollama_client.post(
                url,
                json=payload,
                **request_options,
            )
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                answer = message.get("content")
                if answer:
                    return answer, AI_SOURCE_OLLAMA
        except Exception:
            pass
        return None, None
