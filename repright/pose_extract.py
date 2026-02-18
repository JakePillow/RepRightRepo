from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def extract_pose_npz(
    video_path: Path,
    exercise: str,
    processed_root: Path = Path("data/processed"),
    *,
    model_complexity: int = 1,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    max_frames: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Extract MediaPipe pose landmarks to NPZ expected by compute_rep_metrics.py.

    Output:
      data/processed/pose/<exercise>/<stem>.npz
      data/processed/pose/<exercise>/<stem>_meta.json
    """

    video_path = Path(video_path)
    processed_root = Path(processed_root)
    ex = (exercise or "").strip().lower()

    out_dir = processed_root / "pose" / ex
    out_dir.mkdir(parents=True, exist_ok=True)

    npz_path = out_dir / f"{video_path.stem}.npz"
    meta_path = out_dir / f"{video_path.stem}_meta.json"

    import cv2
    import mediapipe as mp

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        model_complexity=model_complexity,
        enable_segmentation=False,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    frames = []
    n = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        n += 1
        if max_frames is not None and n > max_frames:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)

        arr = np.full((33, 4), np.nan, dtype=np.float32)

        if res.pose_landmarks:
            lm = res.pose_landmarks.landmark
            for i in range(min(33, len(lm))):
                arr[i, 0] = lm[i].x
                arr[i, 1] = lm[i].y
                arr[i, 2] = getattr(lm[i], "z", np.nan)
                arr[i, 3] = getattr(lm[i], "visibility", np.nan)

        frames.append(arr)

    cap.release()
    pose.close()

    pose_arr = (
        np.stack(frames, axis=0)
        if frames
        else np.zeros((0, 33, 4), dtype=np.float32)
    )

    np.savez_compressed(npz_path, pose=pose_arr)

    meta = {
        "fps": fps,
        "n_frames": int(pose_arr.shape[0]),
        "source_video": str(video_path).replace("\\", "/"),
        "exercise": ex,
    }

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return npz_path, meta_path
