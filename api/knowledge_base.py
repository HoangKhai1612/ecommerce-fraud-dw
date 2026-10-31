"""
Phase 31: Simple knowledge base retrieval from project documentation.

Provides keyword-based retrieval from docs/ directory for system knowledge
queries. No vector database or embeddings - just simple keyword matching
with relevance scoring.
"""
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

# Priority docs for system knowledge queries
PRIORITY_DOCS = [
    "07_architecture/architecture_overview.md",
    "07_architecture/component_architecture.md",
    "07_architecture/data_flow.md",
    "08_data_model/fact_tables.md",
    "08_data_model/dimension_tables.md",
    "08_data_model/data_dictionary.md",
    "12_dbt_models/dbt_models.md",
    "13_airflow/airflow_dag.md",
    "16_machine_learning/machine_learning.md",
    "19_model_integration/model_integration.md",
    "21_fastapi/fastapi.md",
    "22_ai_assistant/ai_assistant.md",
    "23_docker/docker_compose.md",
    "31_integrated_platform/architecture.md",
    "31_integrated_platform/api_reference.md",
]


def _load_doc(path: str) -> str:
    """Load a document file, return empty string if not found."""
    full_path = DOCS_DIR / path
    if full_path.exists():
        try:
            return full_path.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def _score_doc(doc_text: str, keywords: list[str]) -> int:
    """Score a document based on keyword matches."""
    text_lower = doc_text.lower()
    score = 0
    for kw in keywords:
        count = text_lower.count(kw.lower())
        score += count
    return score


def retrieve_knowledge(question: str, max_docs: int = 3, max_chars: int = 3000) -> dict[str, Any]:
    """
    Retrieve relevant documentation snippets for a system knowledge question.

    Returns:
        {
            "sources": [list of doc paths],
            "context": "concatenated relevant text",
            "found": bool
        }
    """
    # Extract keywords from question
    keywords = [w for w in question.lower().split() if len(w) > 2]
    # Add common Vietnamese/English terms
    extra_keywords = []
    q_lower = question.lower()
    if any(w in q_lower for w in ["bang", "table", "schema", "bang du lieu"]):
        extra_keywords.extend(["table", "schema", "marts", "fact", "dimension"])
    if any(w in q_lower for w in ["pipeline", "etl", "dbt", "airflow"]):
        extra_keywords.extend(["pipeline", "etl", "dbt", "airflow", "transform"])
    if any(w in q_lower for w in ["model", "xgboost", "machine learning", "ml"]):
        extra_keywords.extend(["model", "xgboost", "machine learning", "feature"])
    if any(w in q_lower for w in ["kien truc", "architecture", "he thong"]):
        extra_keywords.extend(["architecture", "system", "component"])
    keywords = list(set(keywords + extra_keywords))

    # Score all priority docs
    scored = []
    for doc_path in PRIORITY_DOCS:
        text = _load_doc(doc_path)
        if text:
            score = _score_doc(text, keywords)
            if score > 0:
                scored.append((doc_path, score, text))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return {"sources": [], "context": "", "found": False}

    # Build context from top docs
    context_parts = []
    sources = []
    total_chars = 0
    for doc_path, score, text in scored[:max_docs]:
        if total_chars >= max_chars:
            break
        snippet = text[:max_chars - total_chars]
        context_parts.append(f"--- {doc_path} ---\n{snippet}")
        sources.append(doc_path)
        total_chars += len(snippet)

    return {
        "sources": sources,
        "context": "\n\n".join(context_parts),
        "found": True,
    }


def classify_query(question: str) -> str:
    """
    Classify a question into one of:
    - DATA_QUERY: needs SQL query to database
    - SYSTEM_KNOWLEDGE: needs documentation/knowledge retrieval
    - HYBRID_QUERY: needs both
    - UNSUPPORTED_QUERY: cannot be answered

    Returns the classification string.
    """
    q = question.lower()

    # Data query keywords (Vietnamese + English)
    data_keywords = [
        "bao nhieu", "how many", "count", "tong", "sum",
        "thong ke", "statistics", "phan tram", "percent", "rate",
        "trung binh", "average", "max", "min", "group by",
        "top", "danh sach", "list", "so luong", "so giao dich",
        "gian lan", "fraud", "san pham", "product",
        "tien", "amount", "thoi gian", "time",
    ]

    # System knowledge keywords
    knowledge_keywords = [
        "kien truc", "architecture", "he thong", "system",
        "bang", "table", "schema", "cot", "column",
        "dbt", "airflow", "pipeline", "etl",
        "model", "xgboost", "machine learning",
        "docker", "deployment", "deploy",
        "fastapi", "api", "endpoint",
        "data warehouse", "dw",
        "nguyen ly", "principle", "cach", "how",
        "gi la", "what is", "la gi",
        "vai tro", "role", "muc dich", "purpose",
    ]

    data_score = sum(1 for kw in data_keywords if kw in q)
    knowledge_score = sum(1 for kw in knowledge_keywords if kw in q)

    # Check for data-specific patterns (numbers, aggregations)
    has_aggregation = any(w in q for w in ["bao nhieu", "how many", "count", "tong", "sum", "trung binh", "average", "max", "min", "top"])

    # Check for knowledge-specific patterns
    has_knowledge = any(w in q for w in ["la gi", "what is", "vai tro", "role", "kien truc", "architecture", "cach", "how", "pipeline", "dbt", "airflow"])

    if data_score > 0 and knowledge_score > 0:
        if has_aggregation and has_knowledge:
            return "HYBRID_QUERY"
        elif has_aggregation:
            return "DATA_QUERY"
        elif has_knowledge:
            return "SYSTEM_KNOWLEDGE"
        else:
            return "DATA_QUERY"
    elif data_score > 0:
        return "DATA_QUERY"
    elif knowledge_score > 0:
        return "SYSTEM_KNOWLEDGE"
    else:
        # Default: try data query first
        return "DATA_QUERY"
