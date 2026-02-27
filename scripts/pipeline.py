from __future__ import annotations

import json
import time
from pathlib import Path

import cv2

MIN_VALID_OVERLAY_BYTES = 50 * 1024


def _clamp_rep_frames_inplace(analysis: dict) -> None:
    """
    Clamp per-rep frame indices into [0, n_frames-1] and recompute duration_sec if possible.
    Prevents downstream mismatches when frames go out of bounds.
    """
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
                if v < 0:
                    r[k] = 0
                elif v > max_idx:
                    r[k] = max_idx

        # Keep duration consistent after clamping
        if isinstance(fps, (int, float)) and fps > 0:
            sf = r.get("start_frame")
            ef = r.get("end_frame")
            if isinstance(sf, int) and isinstance(ef, int) and ef >= sf:
                r["duration_sec"] = (ef - sf) / float(fps)


def new_run_dir(video_path: str | Path, exercise: str, processed_root: str | Path = "data/processed") -> Path:
    """
    Create a stable run_dir under:
      <processed_root>/runs/<exercise>/<timestamp>_<safe_stem>

    Accepts str or Path.
    """
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
    """
    Overlay is considered valid if:
      - exists
      - size >= min_bytes
      - cv2 can open and reports frame_count > 0
    """
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
) -> tuple[Path, Path, Path]:
    """
    Canonical pipeline:
      1) extract_all.process_video -> produces poses jsonl + overlay candidate(s) + optional summary
      2) compute_rep_metrics_file -> writes analysis_v1.json
      3) load analysis -> clamp -> attach overlay/artifacts -> rewrite analysis_v1.json

    Returns: (overlay_video_path, analysis_json_path, run_dir)
    """
    video_path = Path(video_path)
    ex = (exercise or "").strip().lower()

    if run_dir is None:
        run_dir_p = new_run_dir(video_path, ex, processed_root=processed_root)
    else:
        run_dir_p = Path(run_dir)
        run_dir_p.mkdir(parents=True, exist_ok=True)

    from scripts import extract_all
    from scripts.compute_rep_metrics import compute_rep_metrics_file

    # 1) Pose extraction + overlay attempt(s)
    extract_all.process_video(video_path, run_dir_p, label_override=ex)

    poses_jsonl = _pick_first(run_dir_p, [f"{video_path.stem}*.jsonl", "*.jsonl"])
    if poses_jsonl is None:
        raise RuntimeError("Pose extraction failed (no jsonl produced).")

    # 2) Pick overlay candidate (may have been generated already in extract_all)
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
        if overlay_video is not None and overlay_video.exists():
            try:
                print(f"[warn] Overlay looks invalid ({overlay_video.stat().st_size} bytes): {overlay_video}")
            except OSError:
                print(f"[warn] Overlay looks invalid: {overlay_video}")
        overlay_video = run_dir_p / "MISSING_OVERLAY.mp4"

    # 3) Determine fps (prefer summary if present)
    summary_json = _pick_first(run_dir_p, [f"{video_path.stem}*_summary.json", "*_summary.json"])
    fps = 25.0
    if summary_json and summary_json.exists():
        try:
            s = json.loads(summary_json.read_text(encoding="utf-8"))
            fps = float(s.get("fps", fps))
        except Exception:
            pass

       # 4) Compute metrics (writes analysis_v1.json)
    metrics_json = run_dir_p / "analysis_v1.json"
    compute_rep_metrics_file(ex, poses_jsonl, metrics_json, fps=fps)

    # 4b) Re-render overlay AFTER metrics exist so HUD can display offline rep count.
    # This will overwrite/refresh the overlay files in run_dir_p.
    try:
        from scripts import extract_all as _extract_all

        _extract_all.process_video(
            video_path,
            run_dir_p,
            label_override=ex,
            analysis_json_path=metrics_json,
        )

        # Re-pick overlay candidate after re-render
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
            if overlay_video is not None and overlay_video.exists():
                try:
                    print(f"[warn] Overlay looks invalid after re-render ({overlay_video.stat().st_size} bytes): {overlay_video}")
                except OSError:
                    print(f"[warn] Overlay looks invalid after re-render: {overlay_video}")
            overlay_video = run_dir_p / "MISSING_OVERLAY.mp4"

    except Exception as e:
        print(f"[warn] Overlay re-render after metrics failed: {e}")

    # 5) Load, clamp, attach overlay + artifacts, and rewrite
    analysis = json.loads(metrics_json.read_text(encoding="utf-8"))
    _clamp_rep_frames_inplace(analysis)

    # Ensure schema marker exists
    analysis.setdefault("schema_version", "analysis_v1")
    analysis.setdefault("exercise", ex)

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