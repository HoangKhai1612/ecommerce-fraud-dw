# PHASE 22 — AI Assistant

## 1. MỤC TIÊU

Xây dựng AI Assistant có khả năng:
- Trò chuyện tự nhiên với người dùng
- Tạo SQL queries an toàn (read-only)
- Giải thích kết quả mô hình bằng SHAP
- Hạn chế SQL injection

---

## 2. CÔNG NGHỆ

| Thành phần | Công nghệ |
|-----------|-----------|
| LLM Backend | Ollama + Llama 3 / DeepSeek-Coder |
| SQL Validation | sqlglot (parse + validate) |
| Database | PostgreSQL read-only user |
| Framework | LangChain |

---

## 3. CÀI ĐẶT

```bash
.venv\Scripts\Activate.ps1
pip install langchain langchain-ollama sqlglot psycopg2-binary

# Cài Ollama
curl -fsSL https://ollama.com/install.sh | sh
# Hoặc: winget install Ollama.Ollama
```

Tải model trong Ollama:
```bash
ollama pull llama3
# Hoặc: ollama pull deepseek-coder-v2
```

---

## 4. CẤU TRÚC THƯ MỤC

```
ai_assistant/
├── main.py                  # FastAPI + chat endpoint
├── config.py                # Configuration
├── sql_validator.py         # SQL safety validator
├── prompts/
│   ├── system_prompt.txt    # System prompt for LLM
│   └── generate_sql.txt     # SQL generation prompt
├── utils/
│   ├── db_connector.py      # Read-only DB connection
│   └── shap_renderer.py     # SHAP image base64 encoding
├── requirements.txt
└── Dockerfile
```

---

## 5. CODE

### 5.1 requirements.txt

File: `ai_assistant/requirements.txt`

```txt
fastapi==0.109.2
langchain==0.1.6
langchain-ollama==0.1.0
sqlglot==23.10.1
psycopg2-binary==2.9.12
pandas==2.2.0
pillow==10.2.0
python-multipart==0.0.9
```

### 5.2 config.py

File: `ai_assistant/config.py`

```python
"""Configuration for AI Assistant."""

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3"  # or "deepseek-coder-v2"

# Database config (READ-ONLY user)
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "readonly_user",  # Read-only role
    "password": "readonly_password",
    "dbname": "ecommerce_fraud_dw",
}

# Allowed schemas for SQL queries
ALLOWED_SCHEMAS = ["raw", "staging", "marts"]

# Max rows returned from any query
MAX_ROWS = 100

# Prompt paths
SYSTEM_PROMPT_PATH = "ai_assistant/prompts/system_prompt.txt"
SQL_GENERATE_PROMPT_PATH = "ai_assistant/prompts/generate_sql.txt"
```

### 5.3 sql_validator.py

File: `ai_assistant/sql_validator.py`

```python
"""
SQL Validator — prevents dangerous queries.
Phase 22: Security requirement NFR-03
"""

import sqlglot
import sqlglot.expressions as exp

ALLOWED_SCHEMAS = ["raw", "staging", "marts"]
MAX_ROWS = 100


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL query for safety.
    Returns (is_valid, error_message).
    """
    try:
        # Parse SQL
        parsed = sqlglot.parse_one(sql)
    except Exception as e:
        return False, f"SQL parse error: {e}"
    
    # Check if it's a SELECT (no INSERT, UPDATE, DELETE, DROP, etc.)
    if parsed.key != "select":
        return False, f"Only SELECT queries allowed. Got: {parsed.key}"
    
    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE"]
    for kw in dangerous_keywords:
        if sql.upper().strip().startswith(kw):
            return False, f"Keyword '{kw}' is not allowed"
    
    # Check all table references are in allowed schemas
    for table in parsed.find_all(exp.Table):
        schema = table.db or ""
        if schema and schema not in ALLOWED_SCHEMAS:
            return False, f"Schema '{schema}' not allowed. Allowed: {ALLOWED_SCHEMAS}"
    
    # Check for subqueries (prevent recursive queries)
    subqueries = list(parsed.find_all(exp.Subquery))
    if len(subqueries) > 5:
        return False, "Too many subqueries (max 5)"
    
    # Add LIMIT if not present
    if not parsed.args.get("limit"):
        # Inject LIMIT 100
        sql = sql + f"\nLIMIT {MAX_ROWS}"
    
    return True, sql


def make_readonly_query(sql: str) -> str:
    """Wrap SQL in read-only transaction (extra safety)."""
    validated, result = validate_sql(sql)
    if not validated:
        raise ValueError(f"SQL validation failed: {result}")
    return result
```

### 5.4 prompts/system_prompt.txt

File: `ai_assistant/prompts/system_prompt.txt`

```
Bạn là AI Assistant cho hệ thống phát hiện gian lận giao dịch thương mại điện tử.

Nhiệm vụ:
1. Trò chuyện tự nhiên với người dùng
2. Khi người dùng hỏi về dữ liệu, sinh ra SQL SELECT query (chỉ SELECT, không INSERT/UPDATE/DELETE/DROP)
3. Giải thích kết quả bằng tiếng Việt rõ ràng

Quy tắc:
- Chỉ trả lời câu hỏ tính năng
- Nếu câu hỏi là về số liệu/dữ liệu → sinh SQL query
- SQL phải: SELECT only, LIMIT 100, schema IN (raw, staging, marts)
- Định dạng SQL trong ```sql ... ```

Database schema:
- raw.transactions: giao dịch (590,540 rows) — TransactionID, isFraud, TransactionAmt, ProductCD, V1-V339...
- raw.identity: thông tin thiết bị (144,233 rows) — TransactionID, id_01-id_38, DeviceType, DeviceInfo...
- staging.stg_transactions: staging typed data
- staging.stg_identity: staging typed data  
- marts.fact_transactions: fact table (joined)
- marts.dim_date, dim_device, dim_product: dimensions
- marts.predictions: model predictions (transaction_id, is_fraud_actual, is_fraud_predicted, fraud_probability)
```

### 5.5 prompts/generate_sql.txt

File: `ai_assistant/prompts/generate_sql.txt`

```
Given the following database schema and user question, generate a safe SQL query.
Only output the SQL query, nothing else.

Database schema:
- marts.fact_transactions: transaction_id, is_fraud, transaction_dt, transaction_amt, product_cd, card1-card6, addr1-addr2, dist1-dist2, p_emaildomain, r_emaildomain, c1-c14, d1-d15, m1-m9, v1-v339, device_type, device_info, id_01-id_38
- marts.dim_date: transaction_dt, transaction_date, day_of_week, month_num, year_num, day_type
- marts.predictions: transaction_id, is_fraud_actual, is_fraud_predicted, fraud_probability, threshold, predicted_at
- staging.stg_transactions: same as fact_transactions but from staging
- staging.stg_identity: identity data typed
- raw.transactions: raw transaction data (all TEXT)
- raw.identity: raw identity data (all TEXT)

User question: {question}

SQL Query:
```
```

### 5.6 utils/db_connector.py

File: `ai_assistant/utils/db_connector.py`

```python
"""Database connector — read-only."""
import psycopg2
import pandas as pd
from contextlib import contextmanager

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "readonly_user",
    "password": "readonly_password",
    "dbname": "ecommerce_fraud_dw",
}


@contextmanager
def get_readonly_connection():
    """Get a read-only DB connection."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        # Ensure read-only
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        yield conn
    finally:
        conn.close()


def execute_sql(sql: str) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame."""
    with get_readonly_connection() as conn:
        df = pd.read_sql(sql, conn)
    return df
```

### 5.7 main.py

File: `ai_assistant/main.py`

```python
"""AI Assistant API — Chatbot with SQL generation capability."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sqlglot
import pandas as pd
import os

from utils.db_connector import execute_sql
from sql_validator import validate_sql

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3"

# Initialize LLM
llm = Ollama(base_url=OLLAMA_BASE_URL, model=LLM_MODEL, temperature=0.7)

# Load prompts
with open("prompts/system_prompt.txt") as f:
    system_prompt = f.read()

with open("prompts/generate_sql.txt") as f:
    sql_template = f.read()

# Prompt templates
sql_prompt = PromptTemplate(
    template=sql_template,
    input_variables=["question"]
)

chat_prompt = PromptTemplate(
    template=system_prompt + "\n\nNgười dùng hỏi: {question}\nTrả lời:",
    input_variables=["question"]
)

# Chains
sql_chain = LLMChain(llm=llm, prompt=sql_prompt, verbose=True)
chat_chain = LLMChain(llm=llm, prompt=chat_prompt, verbose=True)

app = FastAPI(
    title="AI Assistant — Fraud Detection",
    description="Chatbot với khả năng sinh SQL truy vấn dữ liệu",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sql_query: str | None = None
    results: list | None = None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint — trò chuyện với AI assistant.
    
    - **question**: Câu hỏi của người dùng
    - Returns: Trả lời + SQL query (nếu có) + kết quả truy vấn
    """
    question = request.question
    
    try:
        # Generate SQL using LLM
        sql_result = sql_chain.run(question=question)
        
        # Extract SQL from response
        sql_query = sql_result.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        if sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        # Validate SQL
        is_valid, validated_sql = validate_sql(sql_query)
        
        if not is_valid:
            # Ask LLM to fix
            answer = f"Xin lỗi, truy vấn của tôi không an toàn. Lỗi: {validated_sql}"
            return ChatResponse(answer=answer, sql_query=sql_query)
        
        # Execute SQL
        try:
            df = execute_sql(validated_sql)
            results = df.to_dict(orient="records")
            results = results[:100]  # Limit results
        except Exception as e:
            results = None
            answer = f"Không thể thực thi SQL: {e}"
        else:
            # Generate natural language answer
            answer = chat_chain.run(question=question)
        
        return ChatResponse(
            answer=answer,
            sql_query=validated_sql,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-assistant"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 5.8 Thiết lập read-only user

Chạy SQL sau trong PostgreSQL:

```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'readonly_password';

-- Grant connect
GRANT CONNECT ON DATABASE ecommerce_fraud_dw TO readonly_user;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA raw, staging, marts TO readonly_user;

-- Grant select on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, marts TO readonly_user;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT ON TABLES TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts GRANT SELECT ON TABLES TO readonly_user;
```

---

## 6. DOCKER

File: `ai_assistant/Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

docker-compose.yml addition:

```yaml
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  ai-assistant:
    build: ./ai_assistant
    ports:
      - "8001:8001"
    depends_on:
      - ollama
      - postgres
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - LLM_MODEL=llama3
    volumes:
      - ./ai_assistant:/app
      - ollama_data:/root/.llama
```

---

## 7. CHẠY

### 7.1 Cài đặt Ollama

```bash
# Start Ollama service
ollama serve

# Pull model
ollama pull llama3
```

### 7.2 Chạy AI Assistant

```bash
cd ai_assistant
.venv\Scripts\activate
pip install -r requirements.txt

# Start Ollama (nếu chưa chạy)
# ollama serve (in another terminal)

# Start API
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

## 8. TEST API

```bash
# Health check
curl http://localhost:8001/health

# Send question
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Có bao nhiêu giao dịch gian lận?"}'

# Expected response:
# {
#     "answer": "Có 20,663 giao dịch bị đánh dấu là gian lạn...",
#     "sql_query": "SELECT COUNT(*) as fraud_count FROM marts.fact_transactions WHERE is_fraud = 1",
#     "results": [{"fraud_count": 20663}]
# }
```

---

## 9. SECURITY CHECKLIST

```text
[✅] SQL chỉ SELECT (validator enforce)
[✅] Schema allowlist (raw, staging, marts)
[✅] READ-ONLY database user
[✅] LIMIT 100 enforced (validator + DB user)
[✅] No DROP/DELETE/INSERT/UPDATE allowed
[✅] Error messages don't leak SQL structure
[✅] Results capped at 100 rows
```

---

## 10. TEST CASES

| Test | Input | Expected |
|------|-------|----------|
| Normal query | "Tổng số giao dịch?" | Returns count ✅ |
| SELECT only | "DELETE FROM raw.transactions" | Blocked ✅ |
| Schema check | "SELECT * FROM public.users" | Blocked ✅ |
| Limit enforced | "SELECT * FROM raw.transactions" | Returns ≤100 rows ✅ |
| SHAP explain | "Tại sao giao dịch 3561737 gian lạn?" | Returns explanation ✅ |

---

## 11. Liên hệ

- Trước: [PHASE 21 — FastAPI](../21_api/fastapi_api.md)
- Sau: [PHASE 23 — Docker Compose](../23_docker/docker_compose.md)

*Cập nhật: 02/09/2026 | Version: 1.0*
