"""
Phase 25 — Ingestion Unit Tests.

Tests the ingestion module functions WITHOUT requiring the source
CSVs or a live database. Uses synthetic data and mocks for DB
interactions where appropriate.

Run from the project root:

    .venv\\Scripts\\python.exe -m pytest tests/test_ingestion.py -v

Design:
- Pure unit tests: no CSV files, no live PostgreSQL.
- Tests validate_identifier, read_csv_header (via tmp CSV),
  check_raw_data_exists logic, and ingestion method selection.
- Does NOT execute the real load_raw.py main() (which would
  DROP+CREATE raw tables).
"""

import csv
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import ingestion.load_raw as ingestion


# ---------------------------------------------------------------------
# validate_identifier
# ---------------------------------------------------------------------


class TestValidateIdentifier:
    """Tests for ingestion.validate_identifier."""

    def test_valid_identifier(self):
        assert ingestion.validate_identifier("transactions") == "transactions"

    def test_valid_identifier_with_underscore(self):
        assert ingestion.validate_identifier("TransactionID") == "TransactionID"

    def test_empty_identifier_rejected(self):
        with pytest.raises(ValueError, match="rỗng"):
            ingestion.validate_identifier("")

    def test_null_byte_rejected(self):
        with pytest.raises(ValueError):
            ingestion.validate_identifier("bad\x00name")


# ---------------------------------------------------------------------
# read_csv_header
# ---------------------------------------------------------------------


class TestReadCsvHeader:
    """Tests for ingestion.read_csv_header."""

    def _write_csv(self, tmp_path: Path, header: list[str], rows=None):
        path = tmp_path / "test.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            if rows:
                writer.writerows(rows)
        return path

    def test_reads_header(self, tmp_path):
        path = self._write_csv(tmp_path, ["TransactionID", "TransactionAmt", "is_fraud"])
        header = ingestion.read_csv_header(path)
        assert header == ["TransactionID", "TransactionAmt", "is_fraud"]

    def test_strips_bom(self, tmp_path):
        path = tmp_path / "bom.csv"
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])
        header = ingestion.read_csv_header(path)
        assert header[0] == "col1"

    def test_empty_csv_rejected(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        with pytest.raises(StopIteration):
            ingestion.read_csv_header(path)

    def test_duplicate_columns_rejected(self, tmp_path):
        path = self._write_csv(tmp_path, ["a", "b", "a"])
        with pytest.raises(ValueError, match="trùng"):
            ingestion.read_csv_header(path)


# ---------------------------------------------------------------------
# check_raw_data_exists logic
# ---------------------------------------------------------------------


class TestCheckRawDataExists:
    """Tests for the idempotency check."""

    def test_returns_true_when_rows_exist(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.scalar_one.return_value = 100
        result = ingestion.check_raw_data_exists(mock_engine, "raw", "transactions")
        assert result is True

    def test_returns_false_when_no_rows(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.scalar_one.return_value = 0
        result = ingestion.check_raw_data_exists(mock_engine, "raw", "transactions")
        assert result is False


# ---------------------------------------------------------------------
# Ingestion method selection
# ---------------------------------------------------------------------


class TestIngestionMethod:
    """Tests for load_csv_to_raw method dispatch."""

    def test_invalid_method_rejected(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("a,b\n1,2\n", encoding="utf-8")
        mock_engine = MagicMock()

        with patch.object(ingestion, "INGESTION_METHOD", "invalid"):
            with pytest.raises(ValueError, match="hợp lệ"):
                ingestion.load_csv_to_raw(
                    mock_engine, csv_path, "raw", "test", 50000
                )

    def test_missing_file_rejected(self, tmp_path):
        mock_engine = MagicMock()
        with pytest.raises(FileNotFoundError):
            ingestion.load_csv_to_raw(
                mock_engine, tmp_path / "nope.csv", "raw", "test", 50000
            )

    def test_empty_file_rejected(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        mock_engine = MagicMock()
        with pytest.raises(ValueError, match="rỗng"):
            ingestion.load_csv_to_raw(mock_engine, path, "raw", "test", 50000)


# ---------------------------------------------------------------------
# verify_row_count
# ---------------------------------------------------------------------


class TestVerifyRowCount:
    def test_matching_count(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.scalar_one.return_value = 590540
        result = ingestion.verify_row_count(
            mock_engine, "raw", "transactions", 590540
        )
        assert result == 590540

    def test_mismatched_count(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.scalar_one.return_value = 100
        result = ingestion.verify_row_count(
            mock_engine, "raw", "transactions", 590540
        )
        assert result == 100


# ---------------------------------------------------------------------
# Constants and configuration
# ---------------------------------------------------------------------


class TestIngestionConfig:
    def test_expected_row_counts(self):
        assert ingestion.EXPECTED_TRANSACTIONS == 590540
        assert ingestion.EXPECTED_IDENTITY == 144233

    def test_files_to_load_count(self):
        assert len(ingestion.FILES_TO_LOAD) == 2

    def test_file_configs(self):
        txn_config = ingestion.FILES_TO_LOAD[0]
        assert txn_config["csv_file"] == "train_transaction.csv"
        assert txn_config["table_name"] == "transactions"
        assert txn_config["schema"] == "raw"
        assert txn_config["primary_key"] == "TransactionID"

        id_config = ingestion.FILES_TO_LOAD[1]
        assert id_config["csv_file"] == "train_identity.csv"
        assert id_config["table_name"] == "identity"