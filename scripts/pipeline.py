from __future__ import annotations

import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = REPO_ROOT / "storage" / "runs"
RUNS_ROOT.mkdir(parents=True, exist_ok=True)


def new_run_dir(video_path: Path, exercise: str) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_stem = video_path.stem.replace(":", "_").replace("/", "_").replace("\\", "_")
    d = RUNS_ROOT / f"{stamp}_{exercise}_{safe_stem}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pick_first(run_dir: Path, patterns: list[str]) -> Path | None:
    for pat in patterns:
        hits = sorted(run_dir.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    return None


def run_full_pipeline(video_path: Path, exercise: str, run_dir: Path | None = None) -> tuple[Path, Path, Path]:
    run_dir = run_dir or new_run_dir(video_path, exercise)

    from scripts import extract_all
    from scripts.compute_rep_metrics import compute_rep_metrics_file

    extract_all.process_video(video_path, run_dir, label_override=exercise)

    poses_jsonl = _pick_first(run_dir, [f"{video_path.stem}*.jsonl", "*.jsonl"])
    if poses_jsonl is None:
        raise RuntimeError("Pose extraction failed (no jsonl produced).")

    overlay_mp4 = _pick_first(run_dir, [f"{video_path.stem}*_overlay.mp4", "*_overlay.mp4", "*overlay*.mp4"])
    if overlay_mp4 is None:
        overlay_mp4 = run_dir / "MISSING_OVERLAY.mp4"

    summary_json = _pick_first(run_dir, [f"{video_path.stem}*_summary.json", "*_summary.json"])
    fps = 25.0
    if summary_json and summary_json.exists():
        try:
            s = json.loads(summary_json.read_text(encoding="utf-8"))
            fps = float(s.get("fps", fps))
        except Exception:
            pass

    metrics_json = run_dir / "analysis_v1.json"
    compute_rep_metrics_file(exercise, poses_jsonl, metrics_json, fps=fps)
    return overlay_mp4, metrics_json, run_dir
