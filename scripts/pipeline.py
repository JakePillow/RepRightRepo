from __future__ import annotations

import json
import time
from pathlib import Path

import cv2

MIN_VALID_OVERLAY_BYTES = 50 * 1024


def _clamp_rep_frames_inplace(analysis: dict) -> None:
    if not isinstance(analysis, dict):
        return

    reps = analysis.get("reps")
    n_frames = analysis.get("n_frames")
    fps = analysis.get("fps")

    if not isinstance(reps, list) or not isinstance(n_frames, int) or n_frames <= 0:
        return

    max_idx = n_frames - 1
    for r in reps:
        if not isinstance(r, dict):
            continue
        for k in ("start_frame", "peak_frame", "end_frame"):
            v = r.get(k)
            if isinstance(v, int):
                r[k] = max(0, min(max_idx, v))

        if isinstance(fps, (int, float)) and fps > 0:
            sf = r.get("start_frame")
            ef = r.get("end_frame")
            if isinstance(sf, int) and isinstance(ef, int) and ef >= sf:
                r["duration_sec"] = (ef - sf) / float(fps)


def new_run_dir(video_path: str | Path, exercise: str, processed_root: str | Path = "data/processed") -> Path:
    video_path = Path(video_path)
    ex = (exercise or "").strip().lower()
    processed_root = Path(processed_root)

    safe_stem = video_path.stem.replace(":", "_").replace("/", "_").replace("\\", "_")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = processed_root / "runs" / ex / f"{stamp}_{safe_stem}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _pick_first(run_dir: Path, patterns: list[str]) -> Path | None:
    for pat in patterns:
        hits = sorted(run_dir.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    return None


def _is_valid_overlay(path: Path | None, min_bytes: int = MIN_VALID_OVERLAY_BYTES) -> bool:
    if not path or not path.exists():
        return False
    try:
        if path.stat().st_size < min_bytes:
            return False
    except OSError:
        return False

    cap = cv2.VideoCapture(str(path))
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        return frame_count > 0
    finally:
        cap.release()


def run_full_pipeline(
    video_path: str | Path,
    exercise: str,
    run_dir: str | Path | None = None,
    processed_root: str | Path = "data/processed",
) -> tuple[Path | None, Path, Path]:
    video_path = Path(video_path)
    ex = (exercise or "").strip().lower()

    if run_dir is None:
        run_dir_p = new_run_dir(video_path, ex, processed_root=processed_root)
    else:
        run_dir_p = Path(run_dir)
        run_dir_p.mkdir(parents=True, exist_ok=True)

    from scripts import extract_all
    from scripts.compute_rep_metrics import compute_rep_metrics_file

    # 1) extract poses + draft overlay
    extract_all.process_video(video_path, run_dir_p, label_override=ex)

    poses_jsonl = _pick_first(run_dir_p, [f"{video_path.stem}*.jsonl", "*.jsonl"])
    if poses_jsonl is None:
        raise RuntimeError("Pose extraction failed (no jsonl produced).")

    overlay_video = _pick_first(
        run_dir_p,
        [
            f"{video_path.stem}*_overlay.mp4",
            f"{video_path.stem}*_overlay.webm",
            "*_overlay.mp4",
            "*_overlay.webm",
            "*overlay*.mp4",
            "*overlay*.webm",
        ],
    )
    if not _is_valid_overlay(overlay_video):
        overlay_video = None

    # 2) determine fps
    summary_json = _pick_first(run_dir_p, [f"{video_path.stem}*_summary.json", "*_summary.json"])
    fps = 25.0
    if summary_json and summary_json.exists():
        try:
            s = json.loads(summary_json.read_text(encoding="utf-8"))
            fps = float(s.get("fps", fps))
        except Exception:
            pass

    # 3) compute metrics
    metrics_json = run_dir_p / "analysis_v1.json"
    compute_rep_metrics_file(ex, poses_jsonl, metrics_json, fps=fps)

    # 4) re-render overlay with offline analysis hint
    try:
        extract_all.process_video(video_path, run_dir_p, label_override=ex, analysis_json_path=metrics_json)
        candidate = _pick_first(
            run_dir_p,
            [
                f"{video_path.stem}*_overlay.mp4",
                f"{video_path.stem}*_overlay.webm",
                "*_overlay.mp4",
                "*_overlay.webm",
                "*overlay*.mp4",
                "*overlay*.webm",
            ],
        )
        overlay_video = candidate if _is_valid_overlay(candidate) else overlay_video
    except Exception as e:
        print(f"[warn] offline overlay re-render failed: {e}")

    # 5) post-annotate overlay from final analysis reps (single source of truth)
    if overlay_video and _is_valid_overlay(overlay_video):
        try:
            from scripts.annotate_overlay_from_analysis import annotate_overlay

            annotated_target = run_dir_p / f"{video_path.stem}_overlay_annotated.mp4"
            annotated = annotate_overlay(overlay_video, metrics_json, annotated_target)
            overlay_video = annotated if _is_valid_overlay(annotated) else overlay_video
        except Exception as e:
            print(f"[warn] overlay annotation step failed: {e}")

    # 6) load analysis BEFORE clamping (prevents UnboundLocalError)
    analysis = json.loads(metrics_json.read_text(encoding="utf-8"))
    _clamp_rep_frames_inplace(analysis)

    analysis["schema_version"] = "analysis_v1"
    analysis["exercise"] = ex

    overlay_abs = str(overlay_video.resolve()) if _is_valid_overlay(overlay_video) else None
    analysis["overlay_path"] = overlay_abs

    artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}
    artifacts.update(
        {
            "analysis_json": str(metrics_json.resolve()),
            "overlay_path": overlay_abs,
            "metrics_path": str(metrics_json.resolve()),
            "run_dir": str(run_dir_p.resolve()),
        }
    )
    analysis["artifacts_v1"] = artifacts

    metrics_json.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return overlay_video, metrics_json, run_dir_p
