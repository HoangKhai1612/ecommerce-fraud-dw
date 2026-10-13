"""
pytest configuration for Phase 19 tests.

Ensures the project root is on sys.path so tests can
import the ml package when run with:

    .venv\\Scripts\\python.exe -m pytest ml/tests -v
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
