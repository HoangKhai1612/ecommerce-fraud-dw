# 1. MỤC TIÊU

Xây dựng script Python ingestion đọc file CSV từ dataset IEEE-CIS, validate cơ bản, và nạp vào PostgreSQL schema `raw` mà **không biến đổi dữ liệu nghiệp vụ**.

---

# 2. VÌ SAO PHẢI LÀM?

RAW layer là nền tảng của toàn bộ pipeline. Mọi layer phía sau (Staging, DW, ML) đều phụ thuộc vào RAW. Nếu dữ liệu bị lỗi/mất ở RAW, toàn bộ downstream sai.

**Nguyên tắc RAW:**
- Phản ánh dữ liệu nguồn gần nhất có thể
- Không xử lý nghiệp vụ (cleaning, transformation)
- Giữ nguyên schema gốc 100%
- Ghi thêm metadata (load timestamp)

---

# 3. KIẾN THỨC CẦN HỌC

### Kỹ thuật:
- Python `pandas` — đọc CSV theo chunk để xử lý file lớn (652MB)
- `sqlalchemy` — kết nối PostgreSQL, dùng `to_sql()` để load
- `python-dotenv` — quản lý biến môi trường (.env)

### Data Engineering concepts:
- **Chunked loading**: Đọc file CSV theo từng phần (chunksize) để tránh hết RAM
- **Idempotent**: Chạy lại script phải cho kết quả như lần đầu (replace table)
- **Schema**: PostgreSQL schema là namespace, giống database con trong một database

---

# 4. INPUT

| Input | Path | Size |
|-------|------|------|
| Transaction CSV | `data/raw/train_transaction.csv` | 653 MB |
| Identity CSV | `data/raw/train_identity.csv` | 26 MB |

---

# 5. OUTPUT

| Output | PostgreSQL Schema.Table | Rows |
|--------|------------------------|------|
| `raw.transactions` | schema: raw, table: transactions | 590,540 |
| `raw.identity` | schema: raw, table: identity | 144,233 |

---

# 6. KIẾN TRÚC / QUY TRÌNH

```text
CSV files
    ↓
[load_csv_to_raw()]
    ├── Check file exists
    ├── pd.read_csv(chunksize=50000)
    ├── to_sql(if_exists='replace' for first chunk, 'append' for rest)
    └── Log progress
    ↓
[create_raw_schema()]
    └── CREATE SCHEMA IF NOT EXISTS raw
    ↓
[verify_raw_tables()]
    └── SELECT COUNT(*) FROM raw.transactions
    └── SELECT COUNT(*) FROM raw.identity
```

---

# 7. CÁC BƯỚC THỰC HIỆN

## Bước 1: Chuẩn bị môi trường
```powershell
# Kích hoạt virtual environment
.venv\Scripts\Activate.ps1

# Cài đặt packages
pip install -r requirements.txt
```

## Bước 2: Khởi động PostgreSQL
```bash
# Chạy PostgreSQL qua Docker
docker compose up -d postgres
```

## Bước 3: Chạy ingestion script
```bash
python ingestion/load_raw.py
```

## Bước 4: Kiểm tra kết quả
```bash
# Query raw tables
psql -h localhost -U postgres -d ecommerce_fraud_dw -c "SELECT COUNT(*) FROM raw.transactions;"
psql -h localhost -U postgres -d ecommerce_fraud_dw -c "SELECT COUNT(*) FROM raw.identity;"
```

---

# 8. CÔNG CỤ CẦN CÀI

| Công cụ | Version | Install |
|---------|---------|---------|
| Python | 3.10+ | python.org |
| PostgreSQL | 15+ | Docker (postgres:15-alpine) |
| pandas | 2.0+ | pip install pandas |
| SQLAlchemy | 2.0+ | pip install sqlalchemy |
| python-dotenv | 1.0+ | pip install python-dotenv |

---

# 9. TÀI LIỆU CHÍNH THỨC

- pandas read_csv: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- SQLAlchemy: https://docs.sqlalchemy.org/
- PostgreSQL schemas: https://www.postgresql.org/docs/current/ddl-schemas.html

---

# 10. CẤU HÌNH

File `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecommerce_fraud_dw
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATA_DIR=./data/raw
```

---

# 11. CODE

File: `ingestion/load_raw.py`

## Cấu trúc thư mục

```
ingestion/
├── __init__.py          # Empty file (makes Python package)
└── load_raw.py          # Main ingestion script
```

Tạo folder:
```powershell
mkdir ingestion
```

## Code hoàn chỉnh

```python
import os
import csv
import time
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, types as sa_types
from sqlalchemy.engine import URL
from sqlalchemy.engine import Engine

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    psycopg2 = None
    sql = None


# 1. LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# 2. LOAD ENVIRONMENT VARIABLES

load_dotenv()


# 3. DATABASE CONFIGURATION

DB_USER = os.getenv(
    "POSTGRES_USER",
    "postgres"
)

DB_PASS = os.getenv(
    "POSTGRES_PASSWORD",
    "@Melons16122005"
)

DB_NAME = os.getenv(
    "POSTGRES_DB",
    "ecommerce_fraud_dw"
)

DB_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost"
)

DB_PORT = os.getenv(
    "POSTGRES_PORT",
    "5432"
)

DB_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


# 4. INGESTION CONFIGURATION

DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        "./data/raw"
    )
)

INGESTION_METHOD = os.getenv(
    "INGESTION_METHOD",
    "copy"
).lower()

CHUNKSIZE = int(
    os.getenv(
        "INGESTION_CHUNKSIZE",
        "50000"
    )
)

CSV_ENCODING = os.getenv(
    "CSV_ENCODING",
    "utf-8"
)

CSV_DELIMITER = os.getenv(
    "CSV_DELIMITER",
    ","
)


# 5. DATASET CONFIGURATION

EXPECTED_TRANSACTIONS = 590540
EXPECTED_IDENTITY = 144233


FILES_TO_LOAD = [
    {
        "csv_file": "train_transaction.csv",
        "table_name": "transactions",
        "schema": "raw",
        "expected_rows": EXPECTED_TRANSACTIONS,
        "primary_key": "TransactionID",
        "chunksize": CHUNKSIZE,
    },
    {
        "csv_file": "train_identity.csv",
        "table_name": "identity",
        "schema": "raw",
        "expected_rows": EXPECTED_IDENTITY,
        "primary_key": "TransactionID",
        "chunksize": CHUNKSIZE,
    },
]


# 6. DATABASE CONNECTION

def get_db_engine() -> Engine:
    """
    Create SQLAlchemy engine and test PostgreSQL connection.
    """

    logger.info(
        "Đang khởi tạo kết nối PostgreSQL..."
    )

    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,
        future=True
    )

    try:
        with engine.connect() as conn:

            conn.execute(
                text("SELECT 1")
            )

        logger.info(
            "✓ Kết nối PostgreSQL thành công."
        )

        return engine

    except Exception as exc:

        logger.error(
            f"✗ Không thể kết nối PostgreSQL: {exc}"
        )

        engine.dispose()

        raise


# ============================================================
# 7. RAW SCHEMA MANAGEMENT
# ============================================================

def create_raw_schema(
    engine: Engine
) -> None:
    """
    Create RAW schema if it does not exist.
    """

    logger.info(
        "Đang kiểm tra schema 'raw'..."
    )

    with engine.begin() as conn:

        conn.execute(
            text(
                "CREATE SCHEMA IF NOT EXISTS raw"
            )
        )

    logger.info(
        "✓ Schema 'raw' đã sẵn sàng."
    )


# 8. CSV HEADER READING

def read_csv_header(
    csv_path: Path
) -> list[str]:
    """
    Read CSV header without loading the entire dataset.
    """

    logger.info(
        f"Đang đọc header: {csv_path.name}"
    )

    with open(
        csv_path,
        "r",
        encoding=CSV_ENCODING,
        newline=""
    ) as file:

        reader = csv.reader(
            file,
            delimiter=CSV_DELIMITER
        )

        header = next(reader)

    if not header:
        raise ValueError(
            f"CSV không có header: {csv_path}"
        )

    # Remove BOM from first column if present
    header[0] = header[0].lstrip("\ufeff")

    # Remove duplicated column names
    if len(header) != len(set(header)):

        duplicates = [
            column
            for column in set(header)
            if header.count(column) > 1
        ]

        raise ValueError(
            "CSV chứa tên cột bị trùng: "
            f"{duplicates}"
        )

    logger.info(
        f"✓ Phát hiện {len(header):,} cột."
    )

    return header


# 9. SQL IDENTIFIER VALIDATION

def validate_identifier(
    identifier: str
) -> str:
    """
    Validate SQL identifiers used for schema/table/column names.
    """

    if not identifier:
        raise ValueError(
            "SQL identifier không được rỗng."
        )

    if "\x00" in identifier:
        raise ValueError(
            f"SQL identifier không hợp lệ: {identifier}"
        )

    return identifier


# 10. RAW TABLE CREATION

def create_raw_table_from_csv(
    engine: Engine,
    csv_path: Path,
    schema: str,
    table_name: str
) -> list[str]:
    """
    Create RAW table based on CSV header.

    All columns are stored as TEXT in RAW layer.
    """

    schema = validate_identifier(schema)
    table_name = validate_identifier(table_name)

    columns = read_csv_header(
        csv_path
    )

    columns = [
        validate_identifier(column)
        for column in columns
    ]

    logger.info(
        f"Đang tạo bảng {schema}.{table_name}..."
    )

    column_definitions = ", ".join(
        f'"{column.replace(chr(34), chr(34) * 2)}" TEXT'
        for column in columns
    )

    create_sql = (
        f'CREATE TABLE "{schema}"."{table_name}" '
        f'({column_definitions})'
    )

    with engine.begin() as conn:

        conn.execute(
            text(
                f'DROP TABLE IF EXISTS '
                f'"{schema}"."{table_name}" CASCADE'
            )
        )

        conn.execute(
            text(create_sql)
        )

    logger.info(
        f"✓ Đã tạo bảng "
        f"{schema}.{table_name} "
        f"với {len(columns):,} cột TEXT."
    )

    return columns


# 11. FAST COPY INGESTION

def load_csv_with_copy(
    engine: Engine,
    csv_path: Path,
    schema: str,
    table_name: str,
    columns: list[str]
) -> int:
    """
    Fast PostgreSQL COPY ingestion.

    Python streams the CSV directly into PostgreSQL.
    """

    if psycopg2 is None:

        raise ImportError(
            "Chưa cài psycopg2. "
            "Hãy chạy: pip install psycopg2-binary"
        )

    start_time = time.time()

    logger.info(
        f"🚀 COPY MODE: "
        f"{csv_path.name} → {schema}.{table_name}"
    )

    raw_connection = None
    cursor = None

    try:

        raw_connection = engine.raw_connection()

        cursor = raw_connection.cursor()

        quoted_columns = ", ".join(
            f'"{column.replace(chr(34), chr(34) * 2)}"'
            for column in columns
        )

        copy_command = (
            f'COPY "{schema}"."{table_name}" '
            f'({quoted_columns}) '
            f'FROM STDIN '
            f'WITH ('
            f'FORMAT CSV, '
            f'HEADER TRUE, '
            f'DELIMITER \'{CSV_DELIMITER}\', '
            f'QUOTE \'"\', '
            f'ESCAPE \'"\', '
            f'NULL \'\''
            f')'
        )

        with open(
            csv_path,
            "r",
            encoding=CSV_ENCODING,
            newline=""
        ) as csv_file:

            cursor.copy_expert(
                copy_command,
                csv_file
            )

        raw_connection.commit()

        elapsed = time.time() - start_time

        logger.info(
            f"✓ COPY hoàn thành "
            f"trong {elapsed:.2f} giây."
        )

        return 1

    except Exception as exc:

        if raw_connection is not None:
            raw_connection.rollback()

        logger.error(
            f"✗ COPY ingestion thất bại: {exc}"
        )

        raise

    finally:

        if cursor is not None:
            cursor.close()

        if raw_connection is not None:
            raw_connection.close()


# 12. FALLBACK TO_SQL INGESTION

def load_csv_with_to_sql(
    engine: Engine,
    csv_path: Path,
    schema: str,
    table_name: str,
    chunksize: int
) -> int:
    """
    Fallback ingestion using Pandas + SQLAlchemy.

    This method is slower than PostgreSQL COPY,
    but useful as a compatibility fallback.
    """

    start_time = time.time()

    total_rows = 0

    logger.info(
        f"🐢 TO_SQL MODE: "
        f"{csv_path.name} → {schema}.{table_name}"
    )

    chunk_iterator = pd.read_csv(
        csv_path,
        chunksize=chunksize,
        low_memory=False,
        encoding=CSV_ENCODING
    )

    for chunk_index, chunk in enumerate(
        chunk_iterator
    ):

        if_exists = (
            "append"
            if chunk_index > 0
            else "append"
        )

        chunk.to_sql(
            name=table_name,
            schema=schema,
            con=engine,
            if_exists=if_exists,
            method="multi",
            index=False,
            dtype={
                column: sa_types.TEXT
                for column in chunk.columns
            }
        )

        total_rows += len(chunk)

        logger.info(
            f"Đã nạp "
            f"{total_rows:,} bản ghi "
            f"vào {schema}.{table_name}"
        )

    elapsed = time.time() - start_time

    logger.info(
        f"✓ TO_SQL hoàn thành: "
        f"{total_rows:,} bản ghi "
        f"trong {elapsed:.2f} giây."
    )

    return total_rows


# 13. MAIN INGESTION ROUTER

def load_csv_to_raw(
    engine: Engine,
    csv_path: Path,
    schema: str,
    table_name: str,
    chunksize: int
) -> int:
    """
    Main ingestion function.

    COPY is used by default.
    TO_SQL is available as fallback.
    """

    if not csv_path.exists():

        raise FileNotFoundError(
            f"Không tìm thấy file: {csv_path}"
        )

    if csv_path.stat().st_size == 0:

        raise ValueError(
            f"File CSV rỗng: {csv_path}"
        )

    file_size_mb = (
        csv_path.stat().st_size
        / (1024 * 1024)
    )

    logger.info(
        f"File: {csv_path.name}"
    )

    logger.info(
        f"Kích thước: "
        f"{file_size_mb:.2f} MB"
    )

    columns = create_raw_table_from_csv(
        engine=engine,
        csv_path=csv_path,
        schema=schema,
        table_name=table_name
    )

    if INGESTION_METHOD == "copy":

        try:

            load_csv_with_copy(
                engine=engine,
                csv_path=csv_path,
                schema=schema,
                table_name=table_name,
                columns=columns
            )

        except Exception as exc:

            logger.warning(
                "COPY thất bại. "
                "Chuyển sang TO_SQL fallback."
            )

            logger.warning(
                f"Lý do: {exc}"
            )

            # Recreate empty table before fallback
            create_raw_table_from_csv(
                engine=engine,
                csv_path=csv_path,
                schema=schema,
                table_name=table_name
            )

            return load_csv_with_to_sql(
                engine=engine,
                csv_path=csv_path,
                schema=schema,
                table_name=table_name,
                chunksize=chunksize
            )

        return 1

    if INGESTION_METHOD == "to_sql":

        return load_csv_with_to_sql(
            engine=engine,
            csv_path=csv_path,
            schema=schema,
            table_name=table_name,
            chunksize=chunksize
        )

    raise ValueError(
        "INGESTION_METHOD không hợp lệ: "
        f"{INGESTION_METHOD}. "
        "Chỉ hỗ trợ: copy hoặc to_sql."
    )


# 14. ROW COUNT VALIDATION

def verify_row_count(
    engine: Engine,
    schema: str,
    table_name: str,
    expected_rows: int
) -> int:
    """
    Verify actual PostgreSQL row count.
    """

    query = text(
        f'SELECT COUNT(*) '
        f'FROM "{schema}"."{table_name}"'
    )

    with engine.connect() as conn:

        actual_rows = conn.execute(
            query
        ).scalar_one()

    if actual_rows == expected_rows:

        logger.info(
            f"✓ {schema}.{table_name}: "
            f"{actual_rows:,} bản ghi "
            f"(đúng expected)"
        )

    else:

        logger.warning(
            f"✗ {schema}.{table_name}: "
            f"{actual_rows:,} bản ghi "
            f"(Expected: {expected_rows:,})"
        )

    return actual_rows


# 15. PRIMARY KEY / TRANSACTION ID VALIDATION

def verify_primary_key(
    engine: Engine,
    schema: str,
    table_name: str,
    primary_key: str | None
) -> None:
    """
    Check NULL and duplicate values of the logical key.
    """

    if not primary_key:

        logger.info(
            f"Không cấu hình primary key cho "
            f"{schema}.{table_name}."
        )

        return

    escaped_key = primary_key.replace(
        '"',
        '""'
    )

    escaped_schema = schema.replace(
        '"',
        '""'
    )

    escaped_table = table_name.replace(
        '"',
        '""'
    )

    null_query = text(
        f'SELECT COUNT(*) '
        f'FROM "{escaped_schema}"."{escaped_table}" '
        f'WHERE "{escaped_key}" IS NULL'
    )

    duplicate_query = text(
        f'SELECT COUNT(*) '
        f'FROM ('
        f'    SELECT "{escaped_key}" '
        f'    FROM "{escaped_schema}"."{escaped_table}" '
        f'    GROUP BY "{escaped_key}" '
        f'    HAVING COUNT(*) > 1'
        f') AS duplicates'
    )

    with engine.connect() as conn:

        null_count = conn.execute(
            null_query
        ).scalar_one()

        duplicate_count = conn.execute(
            duplicate_query
        ).scalar_one()

    if null_count == 0:

        logger.info(
            f"✓ {schema}.{table_name}: "
            f"{primary_key} không có NULL."
        )

    else:

        logger.warning(
            f"⚠ {schema}.{table_name}: "
            f"{null_count:,} NULL "
            f"ở {primary_key}."
        )

    if duplicate_count == 0:

        logger.info(
            f"✓ {schema}.{table_name}: "
            f"Không phát hiện duplicate {primary_key}."
        )

    else:

        logger.warning(
            f"⚠ {schema}.{table_name}: "
            f"{duplicate_count:,} giá trị duplicate "
            f"ở {primary_key}."
        )


# 16. RAW DATA VALIDATION

def verify_raw_tables(
    engine: Engine
) -> None:
    """
    Verify all RAW tables after ingestion.
    """

    logger.info("")
    logger.info(
        "=" * 60
    )

    logger.info(
        "KIỂM TRA DỮ LIỆU TẠI RAW LAYER"
    )

    logger.info(
        "=" * 60
    )

    all_valid = True

    for file_config in FILES_TO_LOAD:

        schema = file_config["schema"]

        table_name = file_config["table_name"]

        expected_rows = file_config[
            "expected_rows"
        ]

        primary_key = file_config.get(
            "primary_key"
        )

        try:

            actual_rows = verify_row_count(
                engine=engine,
                schema=schema,
                table_name=table_name,
                expected_rows=expected_rows
            )

            if actual_rows != expected_rows:
                all_valid = False

            verify_primary_key(
                engine=engine,
                schema=schema,
                table_name=table_name,
                primary_key=primary_key
            )

        except Exception as exc:

            all_valid = False

            logger.error(
                f"✗ Validation thất bại "
                f"cho {schema}.{table_name}: "
                f"{exc}"
            )

    logger.info(
        "=" * 60
    )

    if all_valid:

        logger.info(
            "✓ RAW DATA VALIDATION: PASSED"
        )

    else:

        logger.warning(
            "⚠ RAW DATA VALIDATION: "
            "CÓ VẤN ĐỀ CẦN KIỂM TRA"
        )

    logger.info(
        "=" * 60
    )


# 17. FILE SIZE INFORMATION

def log_dataset_information(
    csv_path: Path
) -> None:
    """
    Log basic information about input CSV.
    """

    size_bytes = csv_path.stat().st_size

    size_mb = (
        size_bytes
        / (1024 * 1024)
    )

    size_gb = (
        size_bytes
        / (1024 * 1024 * 1024)
    )

    logger.info(
        f"Dataset: {csv_path.name}"
    )

    logger.info(
        f"Size: {size_mb:.2f} MB "
        f"({size_gb:.3f} GB)"
    )


# 18. MAIN PIPELINE

def main() -> None:
    """
    Execute the complete RAW ingestion pipeline.
    """

    pipeline_start = time.time()

    logger.info("")
    logger.info(
        "=" * 70
    )

    logger.info(
        "BẮT ĐẦU DATA INGESTION PIPELINE"
    )

    logger.info(
        "IEEE-CIS FRAUD DETECTION DATASET"
    )

    logger.info(
        "=" * 70
    )

    logger.info(
        f"DATA_DIR: {DATA_DIR}"
    )

    logger.info(
        f"INGESTION_METHOD: {INGESTION_METHOD}"
    )

    logger.info(
        f"CHUNKSIZE: {CHUNKSIZE:,}"
    )

    logger.info(
        f"DATABASE: {DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    engine = None

    try:

        # ----------------------------------------------------
        # STEP 1: DATABASE CONNECTION
        # ----------------------------------------------------

        engine = get_db_engine()

        # ----------------------------------------------------
        # STEP 2: CREATE RAW SCHEMA
        # ----------------------------------------------------

        create_raw_schema(
            engine
        )

        # ----------------------------------------------------
        # STEP 3: LOAD EACH DATASET
        # ----------------------------------------------------

        for index, file_config in enumerate(
            FILES_TO_LOAD,
            start=1
        ):

            csv_file = file_config[
                "csv_file"
            ]

            table_name = file_config[
                "table_name"
            ]

            schema = file_config[
                "schema"
            ]

            expected_rows = file_config[
                "expected_rows"
            ]

            chunksize = file_config[
                "chunksize"
            ]

            csv_path = (
                DATA_DIR
                / csv_file
            )

            logger.info("")
            logger.info(
                "-" * 70
            )

            logger.info(
                f"DATASET {index}/"
                f"{len(FILES_TO_LOAD)}"
            )

            logger.info(
                f"CSV: {csv_file}"
            )

            logger.info(
                f"TARGET: "
                f"{schema}.{table_name}"
            )

            logger.info(
                f"EXPECTED ROWS: "
                f"{expected_rows:,}"
            )

            logger.info(
                "-" * 70
            )

            # Check file
            if not csv_path.exists():

                raise FileNotFoundError(
                    f"File không tìm thấy: "
                    f"{csv_path}"
                )

            log_dataset_information(
                csv_path
            )

            # Ingestion
            load_csv_to_raw(
                engine=engine,
                csv_path=csv_path,
                schema=schema,
                table_name=table_name,
                chunksize=chunksize
            )

            # Immediate validation
            verify_row_count(
                engine=engine,
                schema=schema,
                table_name=table_name,
                expected_rows=expected_rows
            )

        # ----------------------------------------------------
        # STEP 4: FINAL VALIDATION
        # ----------------------------------------------------

        verify_raw_tables(
            engine
        )

        # ----------------------------------------------------
        # STEP 5: PIPELINE SUMMARY
        # ----------------------------------------------------

        total_elapsed = (
            time.time()
            - pipeline_start
        )

        logger.info("")
        logger.info(
            "=" * 70
        )

        logger.info(
            "✓ DATA INGESTION PIPELINE "
            "HOÀN THÀNH"
        )

        logger.info(
            f"TOTAL TIME: "
            f"{total_elapsed:.2f} giây "
            f"({total_elapsed / 60:.2f} phút)"
        )

        logger.info(
            "RAW LAYER: READY"
        )

        logger.info(
            "NEXT STEP: "
            "dbt STAGING TRANSFORMATION"
        )

        logger.info(
            "=" * 70
        )

    except Exception as exc:

        logger.error("")
        logger.error(
            "=" * 70
        )

        logger.error(
            "✗ DATA INGESTION PIPELINE "
            "THẤT BẠI"
        )

        logger.error(
            f"Lỗi: {exc}"
        )

        logger.error(
            "=" * 70
        )

        raise

    finally:

        if engine is not None:

            engine.dispose()

            logger.info(
                "Đã đóng connection pool PostgreSQL."
            )


# ============================================================
# 19. ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
```


### Code review:

| Thành phần | Đã có? | Ghi chú |
|-----------|--------|---------|
| Logging | ✅ | Có, chi tiết |
| Error handling | ✅ | Có try/except |
| File validation | ✅ | Check os.path.exists |
| Chunked loading | ✅ | chunksize=50000 |
| Schema creation | ✅ | CREATE SCHEMA IF NOT EXISTS |
| Row count verification | ✅ | verify_raw_tables() |
| Configuration via .env | ✅ | load_dotenv() |
| Chunk append | ✅ | first_chunk logic |

---

# 12. GIẢI THÍCH CODE

### `get_db_engine()`
- Tạo SQLAlchemy engine từ DB_URL
- Test kết nối với `SELECT 1`
- Trả về engine nếu thành công, raise exception nếu lỗi

### `create_raw_schema(engine)`
- Tạo schema `raw` nếu chưa tồn tại
- Dùng `engine.begin()` để auto-commit transaction

### `load_csv_to_raw(engine, csv_filename, table_name, chunksize=50000)`
- Đọc file CSV theo chunk để tránh hết RAM
- Chunk đầu tiên dùng `if_exists='replace'` (tạo mới table)
- Các chunk tiếp theo dùng `if_exists='append'`
- Log số dòng đã load

### `verify_raw_tables(engine)`
- Đếm số dòng trong `raw.transactions` và `raw.identity`
- So sánh với expected row count

### `main()`
- Gọi lần lượt: get_db_engine → create_raw_schema → load transactions → load identity → verify

---

# 13. CÁCH CHẠY

```bash
# 1. Khởi động PostgreSQL
docker compose up -d postgres

# 2. Đợi PostgreSQL ready (healthcheck)
# Kiểm tra: docker compose logs postgres

# 3. Chạy ingestion
.venv\Scripts\Activate.ps1
python ingestion/load_raw.py
```

---

# 14. EXPECTED OUTPUT

```text
=== BẮT ĐẦU QUY TRÌNH DATA INGESTION (RAW LAYER) ===
2026-09-02 [...] [INFO] Kết nối tới PostgreSQL thành công!
2026-09-02 [...] [INFO] Đang kiểm tra/khởi tạo schema 'raw'...
2026-09-02 [...] [INFO] Schema 'raw' đã sẵn sàng.
2026-09-02 [...] [INFO] Bắt đầu nạp file train_transaction.csv vào bảng raw.transactions...
2026-09-02 [...] [INFO] Đã nạp 50,000 bản ghi vào raw.transactions...
2026-09-02 [...] [INFO] Đã nạp 100,000 bản ghi vào raw.transactions...
...
2026-09-02 [...] [INFO] Đã nạp 50,000 bản ghi vào raw.identity...
...
2026-09-02 [...] [INFO] Hoàn thành nạp 590,540 bản ghi vào raw.transactions trong XX.XX giây.
2026-09-02 [...] [INFO] Hoàn thành nạp 144,233 bản ghi vào raw.identity trong XX.XX giây.
2026-09-02 [...] [INFO] === KIỂM TRA SỐ LƯỢNG BẢN GHI TẠI RAW LAYER ===
2026-09-02 [...] [INFO] -> raw.transactions: 590,540 bản ghi
2026-09-02 [...] [INFO] -> raw.identity:     144,233 bản ghi
2026-09-02 [...] [INFO] === QUY TRÌNH INGESTION HOÀN THÀNH THÀNH CÔNG ===
```

---

# 15. TEST

File: `tests/test_ingestion.py`

## Cấu trúc thư mục

```
tests/
├── __init__.py
└── test_ingestion.py
```

Tạo folder:
```powershell
mkdir tests
```

## Code test đầy đủ

```python
"""
Tests cho Phase 9 — Data Ingestion (RAW Layer)
Chạy: pytest tests/test_ingestion.py -v
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', '@Melons16122005')
DB_NAME = os.getenv('POSTGRES_DB', 'ecommerce_fraud_dw')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DATA_DIR = os.getenv('DATA_DIR', './data/raw')

DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

EXPECTED_TRANSACTIONS = 590540
EXPECTED_IDENTITY = 144233


@pytest.fixture
def engine():
    """Fixture: create DB engine for each test."""
    eng = create_engine(DB_URL)
    yield eng
    eng.dispose()


@pytest.fixture
def csv_files():
    """Fixture: list of CSV files in data/raw/."""
    files = os.listdir(DATA_DIR)
    return [f for f in files if f.endswith('.csv')]


class TestCSVPresence:
    """Kiểm tra file CSV tồn tại."""

    def test_train_transaction_exists(self, csv_files):
        assert 'train_transaction.csv' in csv_files, "train_transaction.csv không tìm thấy"

    def test_train_identity_exists(self, csv_files):
        assert 'train_identity.csv' in csv_files, "train_identity.csv không tìm thấy"

    def test_test_transaction_exists(self, csv_files):
        assert 'test_transaction.csv' in csv_files, "test_transaction.csv không tìm thấy"

    def test_test_identity_exists(self, csv_files):
        assert 'test_identity.csv' in csv_files, "test_identity.csv không tìm thấy"


class TestDatabaseConnection:
    """Kiểm tra kết nối PostgreSQL."""

    def test_engine_connection(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1, "Không thể kết nối tới PostgreSQL"


class TestRawSchema:
    """Kiểm tra schema raw."""

    def test_raw_schema_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = 'raw'"
            )).fetchone()
            assert result is not None, "Schema 'raw' không tồn tại"


class TestRawTables:
    """Kiểm tra bảng raw và số lượng bản ghi."""

    def test_transactions_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'raw' AND table_name = 'transactions'"
            )).fetchone()
            assert result is not None, "Bảng raw.transactions không tồn tại"

    def test_identity_exists(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'raw' AND table_name = 'identity'"
            )).fetchone()
            assert result is not None, "Bảng raw.identity không tồn tại"

    def test_transactions_row_count(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM raw.transactions"))
            count = result.fetchone()[0]
            assert count == EXPECTED_TRANSACTIONS, f"Expected {EXPECTED_TRANSACTIONS} rows, got {count}"

    def test_identity_row_count(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM raw.identity"))
            count = result.fetchone()[0]
            assert count == EXPECTED_IDENTITY, f"Expected {EXPECTED_IDENTITY} rows, got {count}"

    def test_transactions_column_count(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'raw' AND table_name = 'transactions'"
            ))
            count = result.fetchone()[0]
            assert count == 394, f"Expected 394 columns, got {count}"

    def test_identity_column_count(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'raw' AND table_name = 'identity'"
            ))
            count = result.fetchone()[0]
            assert count == 41, f"Expected 41 columns, got {count}"

    def test_transactions_no_null_transaction_id(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM raw.transactions WHERE \"TransactionID\" IS NULL"
            ))
            null_count = result.fetchone()[0]
            assert null_count == 0, f"Có {null_count} TransactionID null trong transactions"

    def test_transactions_no_duplicates(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(DISTINCT \"TransactionID\") AS distinct_count, "
                "COUNT(*) AS total_count FROM raw.transactions"
            ))
            distinct_count, total_count = result.fetchone()
            assert distinct_count == total_count, f"Có {total_count - distinct_count} duplicate TransactionID"

    def test_transactions_transaction_id_unique(self, engine):
        """TransactionID trong transactions phải unique."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) - COUNT(DISTINCT \"TransactionID\") FROM raw.transactions"
            ))
            duplicates = result.fetchone()[0]
            assert duplicates == 0, f"Có {duplicates} duplicate TransactionID"

    def test_transactions_all_text_type(self, engine):
        """Tất cả columns trong raw.transactions phải là TEXT (RAW layer)."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = 'raw' AND table_name = 'transactions' "
                "AND data_type != 'text'"
            ))
            non_text = result.fetchone()[0]
            assert non_text == 0, f"Có {non_text} columns không phải TEXT"

    def test_transactions_is_fraud_values(self, engine):
        """isFraud chỉ nhận giá trị 0 hoặc 1."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(DISTINCT \"isFraud\") FROM raw.transactions"
            ))
            distinct_vals = result.fetchone()[0]
            assert distinct_vals == 2, f"isFraud có {distinct_vals} giá trị (expected 2: 0 và 1)"


class TestCSVRowCount:
    """So sánh số dòng CSV vs database."""

    def test_csv_transaction_rows_match_db(self, engine):
        """Số dòng CSV == số dòng DB."""
        csv_path = os.path.join(DATA_DIR, 'train_transaction.csv')
        # Đếm dòng CSV (trừ header)
        csv_count = sum(1 for _ in open(csv_path, 'r')) - 1

        with engine.connect() as conn:
            db_count = conn.execute(text("SELECT COUNT(*) FROM raw.transactions")).fetchone()[0]

        assert csv_count == db_count, f"CSV: {csv_count}, DB: {db_count}"
```

Chạy test:
```bash
pytest tests/test_ingestion.py -v
```

Expected output:
```
tests/test_ingestion.py::TestCSVPresence::test_train_transaction_exists PASSED
tests/test_ingestion.py::TestCSVPresence::test_train_identity_exists PASSED
tests/test_ingestion.py::TestDatabaseConnection::test_engine_connection PASSED
tests/test_ingestion.py::TestRawSchema::test_raw_schema_exists PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_row_count PASSED
tests/test_ingestion.py::TestRawTables::test_identity_row_count PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_column_count PASSED
tests/test_ingestion.py::TestRawTables::test_identity_column_count PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_no_null_transaction_id PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_no_duplicates PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_all_text_type PASSED
tests/test_ingestion.py::TestRawTables::test_transactions_is_fraud_values PASSED
```

---

# 16. ĐIỀU KIỆN SUCCESS

```text
[ ] PostgreSQL container đang chạy
[ ] File CSV tồn tại tại data/raw/
[ ] Ingestion script chạy thành công
[ ] Schema 'raw' được tạo
[ ] Table 'raw.transactions' có 590,540 rows
[ ] Table 'raw.identity' có 144,233 rows
[ ] Schema bảng giống CSV gốc
[ ] Không mất dữ liệu (row count = CSV row count)
[ ] Có logging
```

---

# 17. ĐIỀU KIỆN FAILURE

```text
[ ] PostgreSQL không chạy → "could not connect to server"
[ ] File CSV không tồn tại → "File not found"
[ ] Encoding error → "UnicodeDecodeError"
[ ] Schema/data type mismatch → psycopg2 error
[ ] Row count không khớp → data loss
```

---

# 18. TROUBLESHOOTING

| Vấn đề | Nguyên nhân | Cách giải quyết |
|--------|-------------|-----------------|
| PostgreSQL connection refused | Container chưa chạy | `docker compose up -d postgres` |
| File not found | DATA_DIR sai | Kiểm tra .env, DATA_DIR=./data/raw |
| Memory error | File quá lớn | Đã có chunksize=50000 |
| Table already exists | Re-run script | Script dùng `if_exists='replace'` |
| Encoding error | CSV encoding | Thêm `encoding='utf-8'` hoặc `low_memory=False` |

---

# 19. EVIDENCE CẦN LƯU

- Terminal output của `python ingestion/load_raw.py`
- Screenshot/queries: `SELECT COUNT(*) FROM raw.transactions`
- Screenshot/queries: `SELECT COUNT(*) FROM raw.identity`
- Log file (nếu có)
- `psql -c "\d raw.transactions"` (schema dump)

---

# 20. LIÊN HỆ VỚI BÁO CÁO

- Chapter 4.2 — Data Ingestion
- Chapter 3.2.1 — Phân tích quy trình dữ liệu
- Chapter 3.3.1 — Thiết kế kiến trúc (Data Flow)

---

# 21. CHECKLIST

```text
[ ] Code: ingestion/load_raw.py tồn tại và có logging
[ ] Test: tests/test_ingestion.py được viết
[ ] Docker: PostgreSQL đang chạy
[ ] Chạy script: python ingestion/load_raw.py thành công
[ ] Verify: row count = 590,540 (transactions) + 144,233 (identity)
[ ] Evidence: lưu terminal output + SQL queries
[ ] Docs: docs/09_ingestion/complete
[ ] Git: commit code + test
```

---

# 22. DEFINITION OF DONE

```text
[ ] Objective: CSV nạp được vào PostgreSQL raw schema
[ ] Code: load_raw.py có error handling, logging, chunked loading
[ ] Test: tests/test_ingestion.py PASS (row count, null check)
[ ] Evidence: terminal output + SQL verification
[ ] Failure cases: đã xem xét (file missing, DB down, encoding)
[ ] Documentation: docs/09_ingestion/complete
[ ] Git: committed to repository
```

*Cập nhật: 02/09/2026 | Version: 1.0*


Kết quả:
PS C:\Users\Administrator\Documents\ecommerce-fraud-dw> python ingestion/load_raw.py
2026-09-09 20:32:48 [INFO] 
2026-09-09 20:32:48 [INFO] ======================================================================
2026-09-09 20:32:48 [INFO] BẮT ĐẦU DATA INGESTION PIPELINE
2026-09-09 20:32:48 [INFO] IEEE-CIS FRAUD DETECTION DATASET
2026-09-09 20:32:48 [INFO] ======================================================================
2026-09-09 20:32:48 [INFO] DATA_DIR: data\raw
2026-09-09 20:32:48 [INFO] INGESTION_METHOD: copy
2026-09-09 20:32:48 [INFO] CHUNKSIZE: 50,000
2026-09-09 20:32:48 [INFO] DATABASE: localhost:5432/ecommerce_fraud_dw
2026-09-09 20:32:48 [INFO] Đang khởi tạo kết nối PostgreSQL...
2026-09-09 20:32:49 [INFO] ✓ Kết nối PostgreSQL thành công.
2026-09-09 20:32:49 [INFO] Đang kiểm tra schema 'raw'...
2026-09-09 20:32:49 [INFO] ✓ Schema 'raw' đã sẵn sàng.
2026-09-09 20:32:49 [INFO]
2026-09-09 20:32:49 [INFO] ----------------------------------------------------------------------
2026-09-09 20:32:49 [INFO] DATASET 1/2
2026-09-09 20:32:49 [INFO] CSV: train_transaction.csv
2026-09-09 20:32:49 [INFO] TARGET: raw.transactions
2026-09-09 20:32:49 [INFO] EXPECTED ROWS: 590,540
2026-09-09 20:32:49 [INFO] ----------------------------------------------------------------------
2026-09-09 20:32:49 [INFO] Dataset: train_transaction.csv
2026-09-09 20:32:49 [INFO] Size: 652.26 MB (0.637 GB)
2026-09-09 20:32:49 [INFO] File: train_transaction.csv
2026-09-09 20:32:49 [INFO] Kích thước: 652.26 MB
2026-09-09 20:32:49 [INFO] Đang đọc header: train_transaction.csv
2026-09-09 20:32:49 [INFO] ✓ Phát hiện 394 cột.
2026-09-09 20:32:49 [INFO] Đang tạo bảng raw.transactions...
2026-09-09 20:32:49 [INFO] ✓ Đã tạo bảng raw.transactions với 394 cột TEXT.
2026-09-09 20:32:49 [INFO] 🚀 COPY MODE: train_transaction.csv → raw.transactions
2026-09-09 20:32:58 [INFO] ✓ COPY hoàn thành trong 9.62 giây.
2026-09-09 20:33:02 [INFO] ✓ raw.transactions: 590,540 bản ghi (đúng expected)
2026-09-09 20:33:02 [INFO] 
2026-09-09 20:33:02 [INFO] ----------------------------------------------------------------------
2026-09-09 20:33:02 [INFO] DATASET 2/2
2026-09-09 20:33:02 [INFO] CSV: train_identity.csv
2026-09-09 20:33:02 [INFO] TARGET: raw.identity
2026-09-09 20:33:02 [INFO] EXPECTED ROWS: 144,233
2026-09-09 20:33:02 [INFO] ----------------------------------------------------------------------
2026-09-09 20:33:02 [INFO] Dataset: train_identity.csv
2026-09-09 20:33:02 [INFO] Size: 25.44 MB (0.025 GB)
2026-09-09 20:33:02 [INFO] File: train_identity.csv
2026-09-09 20:33:02 [INFO] Kích thước: 25.44 MB
2026-09-09 20:33:02 [INFO] Đang đọc header: train_identity.csv
2026-09-09 20:33:02 [INFO] ✓ Phát hiện 41 cột.
2026-09-09 20:33:02 [INFO] Đang tạo bảng raw.identity...
2026-09-09 20:33:02 [INFO] ✓ Đã tạo bảng raw.identity với 41 cột TEXT.
2026-09-09 20:33:02 [INFO] 🚀 COPY MODE: train_identity.csv → raw.identity
2026-09-09 20:33:03 [INFO] ✓ COPY hoàn thành trong 0.39 giây.
2026-09-09 20:33:03 [INFO] ✓ raw.identity: 144,233 bản ghi (đúng expected)
2026-09-09 20:33:03 [INFO]
2026-09-09 20:33:03 [INFO] ============================================================
2026-09-09 20:33:03 [INFO] KIỂM TRA DỮ LIỆU TẠI RAW LAYER
2026-09-09 20:33:03 [INFO] ============================================================
2026-09-09 20:33:03 [INFO] ✓ raw.transactions: 590,540 bản ghi (đúng expected)
2026-09-09 20:33:04 [INFO] ✓ raw.transactions: TransactionID không có NULL.
2026-09-09 20:33:04 [INFO] ✓ raw.transactions: Không phát hiện duplicate TransactionID.
2026-09-09 20:33:04 [INFO] ✓ raw.identity: 144,233 bản ghi (đúng expected)
2026-09-09 20:33:04 [INFO] ✓ raw.identity: TransactionID không có NULL.
2026-09-09 20:33:04 [INFO] ✓ raw.identity: Không phát hiện duplicate TransactionID.
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO]
2026-09-09 20:33:04 [INFO] ======================================================================
2026-09-09 20:33:04 [INFO] ✓ DATA INGESTION PIPELINE HOÀN THÀNH
2026-09-09 20:33:04 [INFO] TOTAL TIME: 15.61 giây (0.26 phút)
2026-09-09 20:33:04 [INFO] RAW LAYER: READY
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO]
2026-09-09 20:33:04 [INFO] ======================================================================
2026-09-09 20:33:04 [INFO] ✓ DATA INGESTION PIPELINE HOÀN THÀNH
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO]
2026-09-09 20:33:04 [INFO] ======================================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO]
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO] ✓ RAW DATA VALIDATION: PASSED
2026-09-09 20:33:04 [INFO] ============================================================
2026-09-09 20:33:04 [INFO]
2026-09-09 20:33:04 [INFO] ======================================================================
2026-09-09 20:33:04 [INFO] ✓ DATA INGESTION PIPELINE HOÀN THÀNH
2026-09-09 20:33:04 [INFO] TOTAL TIME: 15.61 giây (0.26 phút)
2026-09-09 20:33:04 [INFO] RAW LAYER: READY
2026-09-09 20:33:04 [INFO] NEXT STEP: dbt STAGING TRANSFORMATION
2026-09-09 20:33:04 [INFO] ======================================================================
2026-09-09 20:33:04 [INFO] Đã đóng connection pool PostgreSQL.
PS C:\Users\Administrator\Documents\ecommerce-fraud-dw>