from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FAULT_CUES = {
    "LOW_ROM": "Aim for fuller range of motion while keeping control.",
    "RUSHED_CONCENTRIC": "Drive up with intent, but avoid jerking the rep.",
    "LUMBAR_FLEXION": "Brace your core and keep a neutral trunk through the pull.",
}


def run_coach(payload: dict[str, Any], mode: str = "stub") -> dict[str, Any]:
    faults_present = sorted({f.get("code") for r in payload.get("rep_table", []) for f in r.get("faults", []) if isinstance(f, dict) and f.get("code")})

    if faults_present:
        lines = [f"- {FAULT_CUES.get(code, f'Address {code}.')}" for code in faults_present]
        response_text = "Top coaching cues:\n" + "\n".join(lines)
    else:
        response_text = "Great set. No specific fault flags were detected in this analysis."

    return {
        "schema_version": "coach_response_v1",
        "mode": mode,
        "response_text": response_text,
        "debug": {"faults_present": faults_present, "n_reps": len(payload.get("rep_table", []))},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    response = run_coach(payload, mode="stub")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(response["response_text"])
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
