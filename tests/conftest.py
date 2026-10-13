"""pytest configuration for Phase 24 end-to-end tests.

Ensures the project root is on sys.path so tests can import
project modules when run with:

    .venv\\Scripts\\python.exe -m pytest tests -v

Also registers the custom --run-pipeline option used by
tests/test_end_to_end.py to opt in to the full pipeline
execution (ML training included).
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_addoption(parser):
    parser.addoption(
        "--run-pipeline",
        action="store_true",
        default=False,
        help="Execute the full pipeline via run_pipeline.py "
        "(long-running: ML training included).",
    )
