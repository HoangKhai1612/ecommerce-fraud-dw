from __future__ import annotations
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def get_env_meta() -> dict:
    try:
        import psutil
        cpu = psutil.cpu_count()
        mem = psutil.virtual_memory().total
    except Exception:
        cpu = os.cpu_count()
        mem = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": cpu,
        "total_mem_bytes": mem,
    }

def write_json(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")

def write_csv(p: Path, rows: list[dict], headers: list[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})
