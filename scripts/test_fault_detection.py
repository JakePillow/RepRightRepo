from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from repright.analyzer import RepRightAnalyzer


VALID_EXERCISES = ["bench", "curl", "deadlift", "squat"]


def _norm_key(k: str) -> str:
    return (k or "").replace("\ufeff", "").strip().lower()


def _read_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({_norm_key(k): v for k, v in (r or {}).items()})
    return rows


def _pick_stable(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    keyed = []
    for row in rows:
        key = f"{(row.get('video_id') or '').strip()}|{(row.get('path') or '').strip()}"
        keyed.append((hashlib.sha1(key.encode('utf-8')).hexdigest(), row))
    keyed.sort(key=lambda x: x[0])
    return [row for _, row in keyed[:n]]


def main() -> None:
    ap = argparse.ArgumentParser(description="Fault detection exercise coverage tester.")
    ap.add_argument("--labels", default="data/eval/ground_truth.csv")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--sample-per-exercise", type=int, default=5)
    ap.add_argument("--out", default="data/eval_final/test_fault_detection.json")
    args = ap.parse_args()

    rows = _read_rows(Path(args.labels))
    repo_root = Path(args.repo_root).resolve()
    analyzer = RepRightAnalyzer()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        ex = (row.get("exercise") or "").strip().lower()
        if ex in VALID_EXERCISES and (row.get("path") or "").strip():
            grouped[ex].append(row)

    out: dict[str, list[dict[str, Any]]] = {ex: [] for ex in VALID_EXERCISES}

    for ex in VALID_EXERCISES:
        chosen = _pick_stable(grouped.get(ex, []), max(0, args.sample_per_exercise))
        print(f"[{ex}] sampled={len(chosen)}")
        for row in chosen:
            video_id = (row.get("video_id") or "").strip()
            video_path = repo_root / (row.get("path") or "")
            if not video_path.exists():
                continue
            analysis = analyzer.run(str(video_path), ex)
            codes = []
            for rep in analysis.get("reps", []) or []:
                rep_codes = [f.get("code") for f in (rep.get("faults_v1") or []) if isinstance(f, dict) and f.get("code")]
                codes.extend(rep_codes)

            print(f"  video_id={video_id} faults={sorted(set(codes)) if codes else []}")
            out[ex].append({"video_id": video_id, "fault_codes": codes})

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
