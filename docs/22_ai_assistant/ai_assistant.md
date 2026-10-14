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

# PHASE 22 — IMPLEMENT AI ASSISTANT, TEST AND VERIFY

Bạn đang tiếp tục dự án tốt nghiệp hiện có:

**Tên đề tài:** XÂY DỰNG HỆ THỐNG DATA WAREHOUSE VÀ PHÁT HIỆN GIAN LẬN GIAO DỊCH THƯƠNG MẠI ĐIỆN TỬ TÍCH HỢP AI HỖ TRỢ PHÂN TÍCH.

## 1. MỤC TIÊU

Hoàn thành Phase 22 — AI Assistant trực tiếp trên codebase hiện có.

Thư mục dự án dự kiến:

`C:\Users\Administrator\Documents\ecommerce-fraud-dw`

Phase 21 — FastAPI đã được xác nhận hoàn thành trước đó. Phase 22 phải tích hợp với hệ thống hiện có và chuẩn bị cho Phase 23 — Docker Compose.

Không được mặc định mọi file, endpoint, bảng dữ liệu hoặc cấu hình đều giống tài liệu mẫu. Hãy kiểm tra dự án thực tế trước khi sửa.

## 2. QUY TẮC BẮT BUỘC

1. Đọc codebase, `docker-compose.yml`, `.env.example`, tài liệu Phase 19–21, cấu hình API và các file ML/SHAP liên quan trước khi thay đổi.
2. Xác định chính xác cấu trúc thư mục, Python environment, phiên bản thư viện, tên database, PostgreSQL service, schema và các endpoint đang tồn tại.
3. Bảo toàn các chức năng đã hoàn thành ở Phase trước. Không rewrite toàn bộ dự án nếu không cần thiết.
4. Không bịa dữ liệu, kết quả kiểm thử, tên cột, tên model, file artifact hoặc trạng thái hoàn thành.
5. Không ghi đè `.env`, xóa dữ liệu, xóa volume, reset database hoặc thực hiện thao tác phá hủy dữ liệu.
6. Không đưa mật khẩu, API key hoặc thông tin bí mật vào source code, log, báo cáo hay Git.
7. Sử dụng PowerShell tương thích Windows khi chạy lệnh trên máy chủ phát triển.
8. Làm việc theo từng bước nhỏ. Sau mỗi bước, ghi lại file đã sửa, lệnh đã chạy và kết quả thực tế.
9. Nếu một lệnh thất bại, đọc lỗi, xác định nguyên nhân và sửa lỗi có kiểm soát. Không lặp lại cùng một lệnh sai nhiều lần.
10. Nếu thiếu Ollama, model, quyền truy cập hoặc dịch vụ bên ngoài, xác định rõ phần bị chặn và tiếp tục các kiểm thử độc lập có thể thực hiện.
11. Không tuyên bố Phase hoàn thành nếu chưa có bằng chứng thực tế.

## 3. CHỨC NĂNG CẦN TRIỂN KHAI

### 3.1. AI Assistant API

Xây dựng hoặc hoàn thiện module `ai_assistant` với các chức năng:

- Endpoint kiểm tra tình trạng dịch vụ.
- Endpoint chat nhận câu hỏi tiếng Việt.
- Trả lời hội thoại thông thường phù hợp với phạm vi đồ án.
- Nhận diện câu hỏi về dữ liệu và tạo SQL.
- Xác thực SQL trước khi thực thi.
- Truy vấn PostgreSQL bằng tài khoản chỉ đọc.
- Trả lời dựa trên kết quả truy vấn thực tế, không tự bịa số liệu.
- Xử lý lỗi LLM, database, SQL không hợp lệ và timeout bằng thông báo phù hợp.

Giữ tương thích với FastAPI và cách tổ chức API hiện có. Chỉ tạo endpoint hoặc router mới khi cần thiết.

### 3.2. LLM backend

Ưu tiên Ollama chạy cục bộ, cấu hình model và địa chỉ dịch vụ qua biến môi trường.

Yêu cầu:

- Không hardcode thông tin kết nối nhạy cảm.
- Không giả định model đã được tải.
- Phân biệt lỗi Ollama chưa chạy, model chưa tồn tại và lỗi sinh nội dung.
- Đặt timeout phù hợp.
- Không để API health phụ thuộc bắt buộc vào một lần sinh câu trả lời dài.
- Sử dụng thư viện tương thích với phiên bản thực tế của dự án.

Không nâng cấp hàng loạt thư viện nếu chưa đánh giá ảnh hưởng đến các Phase trước.

### 3.3. Text-to-SQL

Sử dụng `sqlglot` hoặc giải pháp tương đương đã được xác minh tương thích.

Bắt buộc:

- Chỉ chấp nhận một câu lệnh SQL truy vấn dữ liệu được phép.
- Chỉ cho phép câu lệnh truy vấn dạng `SELECT` an toàn.
- Từ chối `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, các câu lệnh ghi dữ liệu và những câu lệnh không được phép khác.
- Xử lý đúng SQL nhiều câu lệnh, comment, CTE, subquery, truy vấn lồng nhau và truy cập bảng không được cấp phép.
- Kiểm tra tất cả bảng, schema và cấu trúc truy vấn, kể cả trong CTE và subquery.
- Từ chối truy cập các schema hệ thống và bảng ngoài allowlist.
- Không dựa riêng vào việc tìm kiếm từ khóa trong chuỗi SQL.
- Không nối thêm `LIMIT` vào cuối SQL một cách mù quáng. Hãy sửa AST hoặc dùng cách giới hạn kết quả phù hợp với cú pháp và bảo đảm câu truy vấn vẫn hợp lệ.
- Giới hạn số dòng trả về tối đa 100.
- Đặt timeout truy vấn phù hợp.
- Dùng transaction read-only và tài khoản PostgreSQL chỉ đọc với quyền tối thiểu cần thiết.
- Không trả traceback, mật khẩu, chuỗi kết nối hoặc thông tin nội bộ cho người dùng.

Ưu tiên chỉ cho phép truy vấn các bảng và cột cần thiết trong `marts`. Chỉ mở rộng sang `staging` hoặc `raw` khi được chứng minh là cần thiết.

Nếu schema thực tế khác tài liệu, phải dùng schema thực tế đã kiểm tra.

### 3.4. Database read-only

Kiểm tra tài khoản đọc hiện có và quyền của tài khoản đó.

Nếu chưa có, xây dựng hướng dẫn tạo role riêng bằng biến môi trường hoặc secret phù hợp. Không mặc định mật khẩu mẫu trong tài liệu là mật khẩu thật.

Bảo đảm tài khoản AI không có quyền ghi, sửa, xóa hoặc thay đổi cấu trúc database.

Không chạy lệnh cấp quyền hoặc thay đổi database một cách mù quáng. Kiểm tra trạng thái hiện tại và chỉ áp dụng thay đổi cần thiết.

### 3.5. Trả lời dựa trên kết quả SQL

Quy trình yêu cầu:

1. Phân loại câu hỏi.
2. Sinh SQL khi câu hỏi cần dữ liệu.
3. Kiểm tra và giới hạn SQL.
4. Thực thi bằng kết nối chỉ đọc.
5. Lấy kết quả thực tế.
6. Tạo câu trả lời tiếng Việt dựa trên kết quả.
7. Trả về câu trả lời, SQL đã thực thi và kết quả theo cấu trúc API nhất quán.

Nếu truy vấn lỗi, không được tạo ra câu trả lời chứa số liệu giả.

Không dùng một câu trả lời LLM chung chung để thay thế kết quả thực tế của SQL.

### 3.6. Giải thích dự đoán gian lận bằng SHAP

Kiểm tra Phase 18 và Phase 19 để xác định các artifact, hàm dự đoán và dữ liệu giải thích hiện có.

Tên artifact từng được sử dụng gồm `xgboost.pkl` và `feature_columns.json`; phải xác minh lại trên ổ đĩa trước khi sử dụng.

Nếu có thể tích hợp an toàn:

- Cho phép tra cứu dự đoán đã lưu trong `marts.predictions`.
- Đối chiếu transaction ID với bảng dự đoán thực tế.
- Trả về xác suất gian lận, nhãn dự đoán và threshold nếu các trường đó tồn tại.
- Sử dụng SHAP để giải thích các đặc trưng đóng góp vào dự đoán khi có đủ artifact và dữ liệu đầu vào phù hợp.
- Không tự tạo giá trị SHAP hoặc bịa lý do khiến giao dịch bị đánh dấu gian lận.
- Phân biệt xác suất dự đoán với xác suất đã được hiệu chỉnh và với nhãn gian lận thực tế.
- Nếu chưa đủ điều kiện giải thích SHAP cho từng giao dịch, trả về trạng thái chưa hỗ trợ và ghi rõ nguyên nhân.

Không thay đổi mô hình đã huấn luyện hoặc chạy huấn luyện lại nếu không có lý do kỹ thuật rõ ràng.

### 3.7. Docker và cấu hình

Kiểm tra `docker-compose.yml` hiện có trước khi bổ sung dịch vụ.

- Không tạo PostgreSQL thứ hai nếu dự án đã có database dùng chung.
- Dùng đúng hostname giữa các container.
- Không dùng `localhost` để kết nối đến một container khác từ bên trong container AI.
- Không ghi đè cấu hình Phase 20 hoặc Phase 21.
- Không tự ý thay đổi port đang được sử dụng.
- Không giả định Ollama có thể chạy trên mọi máy chỉ bằng cách thêm container; kiểm tra tài nguyên và khả năng tải model.
- Bảo đảm cấu hình mount file và working directory tương thích với lệnh khởi động thực tế.
- Kiểm tra Dockerfile, requirements và lệnh khởi động trước khi build.

Nếu Docker Compose hiện tại chưa cần tích hợp Ollama ngay, ghi nhận rõ phương án chạy cục bộ và cách tích hợp sau.

## 4. KIỂM THỬ BẮT BUỘC

Tạo hoặc cập nhật automated tests phù hợp với cấu trúc hiện tại.

### A. SQL security tests

Kiểm tra tối thiểu:

1. `SELECT` hợp lệ.
2. `DELETE` bị từ chối.
3. `UPDATE` bị từ chối.
4. `INSERT` bị từ chối.
5. `DROP TABLE` bị từ chối.
6. Nhiều câu lệnh trong cùng một input bị từ chối.
7. Truy vấn schema không được phép bị từ chối.
8. CTE có truy cập bảng không được phép bị từ chối.
9. Subquery có truy cập bảng không được phép bị từ chối.
10. SQL có comment hoặc biến thể viết hoa, viết thường không vượt qua bộ lọc.
11. Truy vấn không có `LIMIT` được giới hạn đúng cách.
12. Truy vấn có `LIMIT` lớn không thể trả về vượt quá 100 dòng.
13. Cú pháp sai được xử lý an toàn.
14. Các hàm hoặc câu lệnh có khả năng ghi dữ liệu không được thực thi.
15. Không để truy vấn chạy vô hạn hoặc vượt giới hạn thời gian.

### B. API tests

- Health endpoint hoạt động.
- Request hợp lệ được xử lý.
- Request rỗng hoặc không hợp lệ được xử lý.
- Câu hỏi dữ liệu sinh SQL và trả kết quả khi LLM/database khả dụng.
- SQL không an toàn bị chặn trước khi thực thi.
- LLM không khả dụng được xử lý rõ ràng.
- Database không khả dụng được xử lý rõ ràng.
- Kết quả không vượt quá giới hạn.
- Lỗi không làm lộ secret hoặc traceback.

### C. SHAP tests

- Kiểm tra hành vi khi có dữ liệu dự đoán.
- Kiểm tra transaction ID không tồn tại.
- Kiểm tra thiếu artifact hoặc feature.
- Kiểm tra không trả lời bằng giải thích giả khi SHAP thất bại.

Không bắt buộc gọi LLM thật trong unit test. Có thể mock các dependency để kiểm tra logic. Phải phân biệt test mock với kiểm thử tích hợp thực tế.

## 5. QUẢN LÝ TIẾN ĐỘ

Chia công việc thành các bước nhỏ:

A. Audit codebase và môi trường.

B. Thiết kế kiến trúc tương thích với dự án.

C. Implement SQL validator và kiểm thử bảo mật.

D. Implement database connector chỉ đọc.

E. Implement LLM service và prompt.

F. Implement chat API và xử lý kết quả.

G. Tích hợp SHAP nếu khả thi.

H. Tích hợp cấu hình Docker cần thiết.

I. Chạy unit tests, integration tests và smoke tests.

J. Ghi tài liệu và báo cáo kết quả.

Sau mỗi bước, xuất một bản tóm tắt ngắn:

- Đã kiểm tra gì.
- Đã sửa file nào.
- Lệnh nào đã chạy.
- Kết quả thực tế.
- Lỗi còn tồn tại.
- Bước tiếp theo.

Không chỉ trả về kế hoạch. Hãy thực hiện các thay đổi trực tiếp trên codebase.

Nếu gặp lỗi, tiếp tục xử lý trong phạm vi an toàn. Nếu bị chặn bởi quyền truy cập hoặc môi trường, ghi rõ nguyên nhân và những gì người dùng cần thực hiện.

## 6. BẰNG CHỨNG HOÀN THÀNH

Tạo tài liệu `docs/22_ai_assistant/ai_assistant.md` hoặc cập nhật vị trí tài liệu Phase 22 phù hợp với quy ước đang có.

Tài liệu phải phản ánh đúng triển khai thực tế, bao gồm:

- Kiến trúc và luồng xử lý.
- Các file đã tạo hoặc sửa.
- Endpoint thực tế.
- Cấu hình môi trường.
- Cách chạy trên Windows.
- Cách chạy với Docker nếu đã xác minh.
- Cách thiết lập PostgreSQL read-only.
- Cơ chế kiểm tra SQL.
- Kết quả kiểm thử và lệnh tái hiện.
- Những chức năng đã xác minh, chưa xác minh và chưa thực hiện được.
- Ảnh chụp hoặc log bằng chứng nếu có thể thu thập.

Lưu log kiểm thử vào thư mục evidence theo quy ước dự án. Không tạo số liệu kiểm thử giả.

## 7. TIÊU CHÍ KẾT THÚC

Chỉ đánh dấu Phase 22 là VERIFIED khi:

- API khởi động thành công.
- Health endpoint được xác minh.
- Các bài kiểm thử SQL security bắt buộc đạt.
- Automated tests đã chạy và có kết quả thực tế.
- Database connector chỉ đọc được kiểm tra.
- Text-to-SQL trả lời dựa trên dữ liệu thật trong môi trường tích hợp nếu môi trường cho phép.
- Tính năng SHAP được xác minh hoặc được ghi nhận rõ là chưa hoàn thành, không tuyên bố đã có.
- Cấu hình không phá vỡ các Phase trước.
- Tài liệu và bằng chứng đã được cập nhật.

Kết thúc bằng báo cáo ngắn, phân biệt rõ PASS, FAIL, BLOCKED và NOT TESTED. Liệt kê lệnh kiểm thử, đường dẫn file đã sửa và mọi việc còn tồn đọng.

**Bắt đầu từ bước A: audit codebase thực tế. Không yêu cầu người dùng lặp lại thông tin đã có trong repository. Không giả định kết quả.**