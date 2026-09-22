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