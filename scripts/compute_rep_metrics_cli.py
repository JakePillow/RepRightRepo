from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.compute_rep_metrics import (
    choose_best_signal,
    per_exercise_params,
    detect_reps_low_to_high,
    compute_rep_metrics,
)


def _load_npz_pose(npz_path: Path) -> np.ndarray:
    d = np.load(npz_path, allow_pickle=False)
    for k in ("pose", "arr_0", "keypoints"):
        if k in d:
            return d[k]
    keys = list(d.keys())
    if not keys:
        raise ValueError(f"No arrays found in npz: {npz_path}")
    return d[keys[0]]


def _load_meta(meta_path: Path) -> Dict[str, Any]:
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _infer_fps(meta: Dict[str, Any], fps_arg: float | None) -> float:
    if fps_arg is not None and fps_arg > 0:
        return float(fps_arg)
    for k in ("fps", "video_fps"):
        v = meta.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return 30.0


def run(
    npz_path: Path,
    exercise: str,
    out_path: Path | None,
    meta_path: Path | None,
    fps_arg: float | None,
) -> Path:
    npz_path = npz_path.resolve()
    pose = _load_npz_pose(npz_path)

    meta = _load_meta(meta_path.resolve()) if meta_path else {}
    fps = _infer_fps(meta, fps_arg)

    sig, driver = choose_best_signal(pose, exercise)
    low, high, min_rep_sec = per_exercise_params(exercise)
    reps = detect_reps_low_to_high(sig, fps=fps, low=low, high=high, min_rep_sec=min_rep_sec)

    metrics_out = compute_rep_metrics(sig, reps, fps, pose=pose, exercise=exercise, low=low, high=high)

    payload: Dict[str, Any] = {
        "schema_version": "analysis_v1",
        "exercise": exercise,
        "driver": driver,
        "source_npz": str(npz_path).replace("\\", "/"),
        "source_meta": str(meta_path).replace("\\", "/") if meta_path else None,
        "fps": float(fps),
        "n_frames": int(pose.shape[0]),
        "n_reps": int(len(metrics_out.get("reps", []))),
        "reps": metrics_out.get("reps", []),
        "set_summary_v1": metrics_out.get("set_summary_v1", {}),
    }

    if out_path is None:
        out_path = npz_path.with_suffix("").with_name(npz_path.stem + "_metrics.json")
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="RepRight compute_rep_metrics CLI wrapper (analysis_v1).")
    ap.add_argument("--npz", required=True, help="Path to pose .npz (data/processed/pose/... .npz)")
    ap.add_argument("--exercise", required=True, help="Exercise label (curl, bench, squat, ...)")
    ap.add_argument("--meta", default=None, help="Optional meta .json containing fps etc.")
    ap.add_argument("--fps", type=float, default=None, help="Override fps (otherwise from meta, else 30)")
    ap.add_argument("--out", default=None, help="Output metrics json path (optional)")
    args = ap.parse_args()

    npz = Path(args.npz)
    meta = Path(args.meta) if args.meta else None
    out = Path(args.out) if args.out else None

    p = run(npz, args.exercise, out, meta, args.fps)
    print(str(p).replace("\\", "/"))


if __name__ == "__main__":
    main()