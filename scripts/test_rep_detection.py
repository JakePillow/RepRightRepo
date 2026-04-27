from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from repright.analyser import RepRightAnalyzer


VALID_EXERCISES = {"bench", "curl", "deadlift", "squat"}


def _norm_key(k: str) -> str:
    return (k or "").replace("\ufeff", "").strip().lower()


def _read_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({_norm_key(k): v for k, v in (r or {}).items()})
    return rows


def _stable_sample(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    scored = []
    for r in rows:
        key = f"{(r.get('video_id') or '').strip()}|{(r.get('path') or '').strip()}"
        h = hashlib.sha1(key.encode("utf-8")).hexdigest()
        scored.append((h, r))
    scored.sort(key=lambda x: x[0])
    return [r for _, r in scored[:n]]


def main() -> None:
    ap = argparse.ArgumentParser(description="Rep detection smoke tester (stable random-like sample).")
    ap.add_argument("--labels", default="data/eval/ground_truth.csv")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--sample-size", type=int, default=10)
    ap.add_argument("--out", default="data/eval_final/test_rep_detection.json")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    rows = _read_rows(Path(args.labels))
    candidates = [
        r for r in rows
        if (r.get("exercise") or "").strip().lower() in VALID_EXERCISES
        and (r.get("path") or "").strip()
    ]

    sample = _stable_sample(candidates, max(0, args.sample_size))
    analyzer = RepRightAnalyzer()

    output: list[dict[str, Any]] = []

    for row in sample:
        video_id = (row.get("video_id") or "").strip()
        exercise = (row.get("exercise") or "").strip().lower()
        vp = repo_root / (row.get("path") or "")
        if not vp.exists():
            continue

        analysis = analyzer.run(str(vp), exercise)
        reps = analysis.get("reps") or []
        rep_snaps = []
        for rep in reps:
            rep_snaps.append(
                {
                    "rep_index": rep.get("rep_index"),
                    "duration_sec": rep.get("duration_sec"),
                    "rom": rep.get("rom"),
                }
            )

        print(f"video_id={video_id} exercise={exercise} predicted_reps={len(reps)}")
        for snap in rep_snaps:
            print(
                f"  rep={snap['rep_index']} duration={snap['duration_sec']:.3f}s rom={snap['rom']:.3f}"
                if isinstance(snap.get("duration_sec"), (int, float)) and isinstance(snap.get("rom"), (int, float))
                else f"  rep={snap.get('rep_index')} duration={snap.get('duration_sec')} rom={snap.get('rom')}"
            )

        output.append(
            {
                "video_id": video_id,
                "exercise": exercise,
                "predicted_reps": len(reps),
                "reps": rep_snaps,
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
