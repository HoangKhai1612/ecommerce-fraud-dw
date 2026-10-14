from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_logging_config_get_logger_no_duplicates(tmp_path, monkeypatch):
    from src import logging_config

    monkeypatch.setattr(logging_config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(logging_config, "LOG_DIR", tmp_path / "logs")

    logger = logging_config.get_logger("test.phase26", "test_phase26.log")
    handlers_before = len(logger.handlers)
    logger2 = logging_config.get_logger("test.phase26", "test_phase26.log")
    handlers_after = len(logger2.handlers)
    assert handlers_before == handlers_after >= 2  # console + file
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)


@pytest.mark.unit
def test_check_logs_handles_missing_files(monkeypatch, capsys, tmp_path):
    from scripts import check_logs

    monkeypatch.setattr(check_logs, "ROOT", tmp_path)
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "missing.log").unlink(missing_ok=True)

    class Args:
        files = ["logs/missing.log"]

    with patch("scripts.check_logs.argparse.ArgumentParser.parse_args", return_value=Args()):
        rc = check_logs.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "SKIP" in out


@pytest.mark.unit
def test_diagnostics_writes_report(tmp_path, monkeypatch):
    from scripts import diagnose_environment

    monkeypatch.setattr(diagnose_environment, "ROOT", tmp_path)
    monkeypatch.setattr(diagnose_environment, "check_port", lambda h, p: diagnose_environment.record(f"TCP {h}:{p}", "WARN", "mocked"))
    monkeypatch.setattr(diagnose_environment, "check_python_packages", lambda: None)
    monkeypatch.setattr(diagnose_environment, "check_postgres", lambda: None)

    (tmp_path / ".env").write_text("dummy", encoding="utf-8")
    (tmp_path / "dbt").mkdir()
    (tmp_path / "dbt" / "dbt_project.yml").write_text("", encoding="utf-8")
    (tmp_path / "ml" / "models").mkdir(parents=True)
    (tmp_path / "ml" / "models" / "xgboost.pkl").write_text("", encoding="utf-8")
    (tmp_path / "ml" / "models" / "feature_columns.json").write_text("{}", encoding="utf-8")

    diagnose_environment.results.clear()
    rc = diagnose_environment.main()
    assert rc in (0, 1)
    out = tmp_path / "evidence" / "phase_26" / "diagnostics.json"
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)
