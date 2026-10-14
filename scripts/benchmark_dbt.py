from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence" / "phase_27"

def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    data = {
        "status": "SKIPPED",
        "reason": "dbt benchmark requires explicit model selection and preflight; not run by default",
        "models": [],
    }
    out = EVID / "dbt_benchmark.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
