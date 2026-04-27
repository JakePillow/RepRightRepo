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


def _stable_pick(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    keyed = []
    for row in rows:
        ex = (row.get("exercise") or "").strip().lower()
        p = (row.get("path") or "").strip()
        if ex not in VALID_EXERCISES or not p:
            continue
        key = f"{(row.get('video_id') or '').strip()}|{p}"
        keyed.append((hashlib.sha1(key.encode("utf-8")).hexdigest(), row))
    keyed.sort(key=lambda x: x[0])
    return keyed[0][1] if keyed else None


def _canonicalize(analysis: dict[str, Any]) -> dict[str, Any]:
    cloned = json.loads(json.dumps(analysis))
    for k in ("timestamp", "video_path", "git_commit", "metrics_path", "overlay_path"):
        cloned.pop(k, None)
    artifacts = cloned.get("artifacts_v1")
    if isinstance(artifacts, dict):
        for k in ("analysis_json", "overlay_path", "metrics_path", "run_dir"):
            artifacts.pop(k, None)
    return cloned


def main() -> None:
    ap = argparse.ArgumentParser(description="Run one video twice and verify stable output.")
    ap.add_argument("--labels", default="data/eval/ground_truth.csv")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out", default="data/eval_final/test_pipeline_consistency.json")
    args = ap.parse_args()

    rows = _read_rows(Path(args.labels))
    target = _stable_pick(rows)
    if target is None:
        raise RuntimeError("No usable video rows found.")

    exercise = (target.get("exercise") or "").strip().lower()
    video_id = (target.get("video_id") or "").strip()
    video_path = Path(args.repo_root).resolve() / (target.get("path") or "")
    if not video_path.exists():
        raise FileNotFoundError(str(video_path))

    analyzer = RepRightAnalyzer()

    run1 = analyzer.run(str(video_path), exercise)
    run2 = analyzer.run(str(video_path), exercise)

    same = _canonicalize(run1) == _canonicalize(run2)
    print(f"video_id={video_id} exercise={exercise} consistent={same}")

    out = {
        "video_id": video_id,
        "exercise": exercise,
        "consistent": bool(same),
        "run1_n_reps": len(run1.get("reps") or []),
        "run2_n_reps": len(run2.get("reps") or []),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path}")

    if not same:
        raise RuntimeError("Pipeline outputs differ between runs for the same input video.")


if __name__ == "__main__":
    main()
