from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


# MediaPipe Pose landmark indices (33)
# We'll draw a basic but clear skeleton:
EDGES = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),          # arms
    (11, 23), (12, 24), (23, 24),                              # torso
    (23, 25), (25, 27), (24, 26), (26, 28),                    # legs
    (27, 31), (28, 32),                                        # feet
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8)  # face-ish
]


def to_pixels(xy: np.ndarray, w: int, h: int) -> np.ndarray:
    """
    xy: (N,2). If it looks normalized (max <= ~2), clamp to [0,1] and scale to pixels.
    If it looks like pixel coords already (max > ~10), keep as-is.
    """
    xy = xy.astype(np.float32)
    mx = float(np.nanmax(xy)) if xy.size else 0.0
    if mx <= 2.5:  # normalized-ish (your y goes to ~1.7)
        xy[:, 0] = np.clip(xy[:, 0], 0.0, 1.0) * float(w)
        xy[:, 1] = np.clip(xy[:, 1], 0.0, 1.0) * float(h)
    return xy


def _find_analysis_json(npz_path: Path, out_path: Path) -> Optional[Path]:
    """
    Your pipeline writes analysis_v1.json in the run_dir. We try to find it without requiring a CLI flag.
    Search order:
      - out_path.parent/analysis_v1.json
      - npz_path.parent/analysis_v1.json
      - parents up to 5 levels from npz_path and out_path
    """
    candidates: List[Path] = []
    candidates.append(out_path.parent / "analysis_v1.json")
    candidates.append(npz_path.parent / "analysis_v1.json")

    for p in out_path.parents:
        candidates.append(p / "analysis_v1.json")
        if len(out_path.parents) > 5 and p == out_path.parents[5]:
            break

    for p in npz_path.parents:
        candidates.append(p / "analysis_v1.json")
        if len(npz_path.parents) > 5 and p == npz_path.parents[5]:
            break

    seen = set()
    for c in candidates:
        if str(c) in seen:
            continue
        seen.add(str(c))
        if c.exists() and c.is_file():
            return c

    return None


def _load_reps_and_exercise(analysis_json: Optional[Path]) -> Tuple[List[Dict[str, Any]], str, bool]:
    if not analysis_json or not analysis_json.exists():
        return [], "", False

    try:
        data = json.loads(analysis_json.read_text(encoding="utf-8"))
    except Exception:
        return [], "", False

    reps = data.get("reps") if isinstance(data, dict) else None
    if not isinstance(reps, list):
        reps = []

    ex = data.get("exercise", "")
    if not isinstance(ex, str):
        ex = ""
    signal_inverted = bool((data.get("rep_debug") or {}).get("signal_inverted"))

    # Only keep dict reps
    reps_out: List[Dict[str, Any]] = []
    for r in reps:
        if isinstance(r, dict):
            reps_out.append(r)
    return reps_out, ex, signal_inverted


def _safe_int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    try:
        iv = int(v)
        return iv
    except Exception:
        return None


def _completion_frame(rep: Dict[str, Any], exercise: str, signal_inverted: bool) -> Optional[int]:
    if exercise == "deadlift" and signal_inverted:
        pf = _safe_int(rep.get("peak_frame"))
        if pf is not None:
            return pf
    return _safe_int(rep.get("end_frame"))


def _clamp_completed_frames(
    reps: List[Dict[str, Any]],
    exercise: str,
    signal_inverted: bool,
    max_frame: int,
) -> List[int]:
    """
    Returns sorted list of completion frames, clamped to [0, max_frame].
    """
    ends: List[int] = []
    for r in reps:
        ef = _completion_frame(r, exercise, signal_inverted)
        if ef is None:
            continue
        if ef < 0:
            ef = 0
        if ef > max_frame:
            ef = max_frame
        ends.append(ef)
    ends.sort()
    return ends


def _draw_counter(frame: np.ndarray, exercise: str, rep_count: int) -> None:
    """
    Draw a simple HUD (top-left). Black box + white text.
    """
    ex_txt = (exercise or "").upper() if exercise else "EXERCISE"
    line1 = f"{ex_txt}"
    line2 = f"Reps: {rep_count}"

    # Box
    x, y = 12, 12
    box_w, box_h = 210, 62
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (0, 0, 0), thickness=-1)
    cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (0, 255, 255), thickness=1)

    # Text
    cv2.putText(frame, line1, (x + 10, y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, line2, (x + 10, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    video_path = Path(args.video)
    npz_path = Path(args.npz)
    out_path = Path(args.out)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    # Try to read video frame count (can be 0/unknown for some files)
    video_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    d = np.load(str(npz_path))
    pose = d["pose"]  # (T,33,4) expected; use [:,:,:2]
    T = int(pose.shape[0])

    # Load reps from analysis_v1.json (auto-discovery)
    analysis_json = _find_analysis_json(npz_path, out_path)
    reps, exercise, signal_inverted = _load_reps_and_exercise(analysis_json)

    # Max valid frame index for rep clamping:
    # - if video frame count is known, clamp to min(video, pose)-1
    # - else clamp to pose length - 1
    if video_frame_count > 0:
        max_valid = max(0, min(video_frame_count, T) - 1)
    else:
        max_valid = max(0, T - 1)

    rep_end_frames = _clamp_completed_frames(reps, exercise, signal_inverted, max_valid)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp_out = out_path.with_name(out_path.stem + ".tmp_mp4v.mp4")
    tmp_out.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(tmp_out), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError("VideoWriter failed to open (mp4v).")

    try:
        t = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # draw skeleton
            if t < T:
                xy = pose[t, :, :2]
                xy = to_pixels(xy, w, h)

                for a, b in EDGES:
                    xa, ya = xy[a]
                    xb, yb = xy[b]
                    if np.isfinite(xa) and np.isfinite(ya) and np.isfinite(xb) and np.isfinite(yb):
                        cv2.line(frame, (int(xa), int(ya)), (int(xb), int(yb)), (0, 255, 0), 2)

                for j in range(min(33, xy.shape[0])):
                    xj, yj = xy[j]
                    if np.isfinite(xj) and np.isfinite(yj):
                        cv2.circle(frame, (int(xj), int(yj)), 4, (0, 0, 255), -1)

            # rep counter (count reps whose end_frame <= current frame)
            rep_count = 0
            if rep_end_frames:
                # ends are sorted; simple scan is fine for small N
                # (If you want, can optimize with bisect, but not needed)
                for ef in rep_end_frames:
                    if t >= ef:
                        rep_count += 1
                    else:
                        break

            _draw_counter(frame, exercise, rep_count)

            writer.write(frame)
            t += 1

    finally:
        cap.release()
        writer.release()

    # Transcode to H.264 for browser/Streamlit reliability
    ff = shutil.which("ffmpeg")
    if ff:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            ff, "-y",
            "-i", str(tmp_out),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        try:
            tmp_out.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        tmp_out.replace(out_path)

    print(str(out_path).replace("\\", "/"))


if __name__ == "__main__":
    main()
