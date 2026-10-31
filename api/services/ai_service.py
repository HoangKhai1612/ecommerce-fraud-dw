"""
Phase 31: AI explanation service.

Builds an explanation request from a REAL prediction record and forwards it
to the AI Assistant service (ai_assistant, port 8001). If the assistant is
unavailable, falls back to calling Ollama directly.
"""

from typing import Any

import httpx

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
        prompt = question or "Giai thich ket qua du doan gian luan nay theo nguyen vao du lieu thuc."
        context = self._build_context(record)
        full_question = f"{prompt}\n\nDu lieu thuc cua du doan:\n{context}"

        answer, source, sql_query, results = self._try_assistant(full_question)
        if answer is not None:
            result = {"answer": answer, "ai_available": True, "source": source}
            if sql_query:
                result["sql_query"] = sql_query
            if results:
                result["results"] = results
            return result

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
    def _build_context(self, record: dict[str, Any]) -> str:
        """Build a plain-text context from the real prediction record."""
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
            for key, value in payload.items():
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

    def _try_assistant(self, question: str) -> tuple[str | None, str | None, str | None, list | None]:
        try:
            url = f"{AI_ASSISTANT_BASE_URL}/chat"
            response = self.assistant_client.post(url, json={"question": question})
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer")
                if answer:
                    return answer, AI_SOURCE_ASSISTANT, data.get("sql_query"), data.get("results")
        except Exception:
            pass
        return None, None, None, None

    def _try_ollama(self, question: str) -> tuple[str | None, str | None]:
        try:
            url = f"{OLLAMA_BASE_URL}/api/chat"
            response = self.ollama_client.post(
                url,
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ban la tro chuyen AI ho tro phan tich gian lban giao dich thuong mai dien tu. Tra loi bang tieng Viet, chi du lieu duoc cung cap, khong bat giat so lieu.",
                        },
                        {"role": "user", "content": question},
                    ],
                    "stream": False,
                },
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
