from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence" / "phase_27"

def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    try:
        import psutil
        proc = psutil.Process()
        rss = proc.memory_info().rss
    except Exception as e:
        rss = None
    data = {
        "status": "SKIPPED" if rss is None else "COMPLETED",
        "reason": "psutil available" if rss is not None else "psutil not available",
        "rss_bytes": rss,
    }
    out = EVID / "memory_profile.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
