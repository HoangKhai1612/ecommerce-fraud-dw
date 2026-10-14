from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "database_connection": re.compile(
        r"connection refused|could not connect|"
        r"connection timed out|operationalerror",
        re.IGNORECASE,
    ),
    "memory": re.compile(
        r"MemoryError|out of memory|OOMKilled",
        re.IGNORECASE,
    ),
    "dbt": re.compile(
        r"Compilation Error|Database Error|"
        r"Completed with \d+ error",
        re.IGNORECASE,
    ),
    "timeout": re.compile(
        r"TimeoutError|timed out|deadline exceeded",
        re.IGNORECASE,
    ),
    "permission": re.compile(
        r"PermissionError|permission denied|"
        r"Access is denied",
        re.IGNORECASE,
    ),
    "model": re.compile(
        r"model file not found|feature names mismatch|"
        r"NotFittedError",
        re.IGNORECASE,
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan project logs for common failure indicators."
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[
            "logs/ingestion.log",
            "logs/ml_train.log",
            "logs/e2e.log",
            "logs/diagnostics.log",
            "dbt/logs/dbt.log",
        ],
        help="Log paths relative to project root.",
    )
    args = parser.parse_args()
    scanned = 0
    matches = 0
    for relative in args.files:
        path = (ROOT / relative).resolve()
        # Prevent reading arbitrary files outside the project root.
        try:
            if not path.is_relative_to(ROOT.resolve()):
                print(f"SKIP: path outside project: {relative}")
                continue
        except Exception:
            print(f"SKIP: path outside project: {relative}")
            continue
        if not path.is_file():
            print(f"SKIP: log not found: {relative}")
            continue
        scanned += 1
        print(f"\n--- {relative} ---")
        try:
            with path.open("r", encoding="utf-8", errors="replace") as stream:
                for line_number, line in enumerate(stream, start=1):
                    categories = [
                        name
                        for name, pattern in PATTERNS.items()
                        if pattern.search(line)
                    ]
                    if categories:
                        matches += 1
                        print(f"Line {line_number}: {', '.join(categories)}")
        except Exception as exc:
            print(f"ERROR reading {relative}: {exc}")
            continue

    print(f"\nScanned files: {scanned}")
    print(f"Matching lines: {matches}")
    print("Review the original logs to determine root cause.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
