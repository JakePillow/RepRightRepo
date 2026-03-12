from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import argparse
import csv
import subprocess
from datetime import datetime, timezone
from typing import Any

import cv2

from repright.analyzer import RepRightAnalyzer

RESULT_FIELDS = [
    "run_id",
    "tag",
    "git_commit",
    "video_id",
    "exercise",
    "path",
    "true_reps",
    "pred_reps",
    "rep_error",
    "abs_error",
    "overlay_valid",
    "overlay_path",
    "inversion",
    "tempo_coverage",
    "n_faults_total",
    "error",
]


def _short_git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
        return out.strip()
    except Exception:
        return "unknown"


def _as_int(value: Any) -> int:
    return int(str(value).strip())


def _overlay_is_valid(path_str: str) -> bool:
    if not path_str:
        return False

    p = Path(path_str)
    if not p.exists() or not p.is_file():
        return False
    if p.stat().st_size < 50 * 1024:
        return False

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        cap.release()
        return False

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return frame_count > 0


def _tempo_coverage(analysis: dict[str, Any]) -> float:
    reps = analysis.get("reps") or []
    if not isinstance(reps, list) or len(reps) == 0:
        return 0.0

    covered = 0
    for rep in reps:
        if not isinstance(rep, dict):
            continue
        if rep.get("tempo_up_sec") is not None and rep.get("tempo_down_sec") is not None:
            covered += 1
    return covered / len(reps)


def _n_faults_total(analysis: dict[str, Any]) -> int:
    reps = analysis.get("reps") or []
    if not isinstance(reps, list):
        return 0
    total = 0
    for rep in reps:
        if isinstance(rep, dict):
            faults = rep.get("faults_v1") or []
            if isinstance(faults, list):
                total += len(faults)
    return total


def _read_ground_truth(ground_path: Path) -> list[dict[str, str]]:
    with ground_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _ensure_results_header(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        return
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        writer.writeheader()


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-evaluate RepRight analyzer outputs against labeled rep counts.")
    parser.add_argument("--ground", required=True, help="Path to ground_truth.csv")
    parser.add_argument("--out", required=True, help="Path to append-only results.csv")
    parser.add_argument("--tag", required=True, help="Run tag (e.g. baseline_v0)")
    args = parser.parse_args()

    ground_path = Path(args.ground)
    out_path = Path(args.out)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    git_commit = _short_git_commit()

    if not ground_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_path}")

    rows = _read_ground_truth(ground_path)
    _ensure_results_header(out_path)

    analyzer = RepRightAnalyzer()

    with out_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS)

        for row in rows:
            base = {
                "run_id": run_id,
                "tag": args.tag,
                "git_commit": git_commit,
                "video_id": (row.get("video_id") or "").strip(),
                "exercise": (row.get("exercise") or "").strip(),
                "path": (row.get("path") or "").strip(),
                "true_reps": (row.get("true_reps") or "").strip(),
                "pred_reps": "",
                "rep_error": "",
                "abs_error": "",
                "overlay_valid": 0,
                "overlay_path": "",
                "inversion": "",
                "tempo_coverage": "",
                "n_faults_total": "",
                "error": "",
            }
            try:
                true_reps = _as_int(base["true_reps"])
                analysis = analyzer.analyze(base["path"], base["exercise"])

                pred_reps = (analysis.get("set_summary_v1") or {}).get("n_reps")
                if pred_reps is None:
                    pred_reps = analysis.get("n_reps")
                pred_reps = _as_int(pred_reps)

                overlay_path = (analysis.get("artifacts_v1") or {}).get("overlay_path")
                if not overlay_path:
                    overlay_path = analysis.get("overlay_path") or ""

                rep_error = pred_reps - true_reps
                inversion = (analysis.get("rep_debug") or {}).get("signal_inverted")
                if inversion is None:
                    inversion = analysis.get("inversion")

                base.update(
                    {
                        "pred_reps": pred_reps,
                        "rep_error": rep_error,
                        "abs_error": abs(rep_error),
                        "overlay_valid": 1 if _overlay_is_valid(str(overlay_path)) else 0,
                        "overlay_path": str(overlay_path),
                        "inversion": 1 if bool(inversion) else 0,
                        "tempo_coverage": f"{_tempo_coverage(analysis):.6f}",
                        "n_faults_total": _n_faults_total(analysis),
                        "error": "",
                    }
                )
            except Exception as exc:
                base["error"] = str(exc)

            writer.writerow(base)

    print(f"[OK] appended {len(rows)} rows to {out_path}")
    print(f"[INFO] run_id={run_id} tag={args.tag} git_commit={git_commit}")


if __name__ == "__main__":
    main()
