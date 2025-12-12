import cv2
import numpy as np
from pathlib import Path
import argparse


# Mediapipe BlazePose-ish 33-landmark skeleton
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 29), (29, 31), (28, 30), (30, 32),
]


def load_pose(npz_path: Path):
    """
    Load landmarks and visibility from the NPZ file.

    Tries a few common key names so it doesn't explode if
    extract_poses.py used 'keypoints' instead of 'landmarks', etc.
    """
    data = np.load(npz_path)

    # Try several possible keys for the coordinates
    coord_keys = ["landmarks", "keypoints", "pose"]
    landmarks = None
    for k in coord_keys:
        if k in data:
            landmarks = data[k]
            break

    if landmarks is None:
        raise KeyError(
            f"None of {coord_keys} found in {npz_path.name}. "
            f"Available keys: {list(data.keys())}"
        )

    # Visibility (or default to all 1s)
    if "visibility" in data:
        visibility = data["visibility"]
    else:
        # shape: (frames, 33, 3) → we want (frames, 33)
        vis_shape = landmarks.shape[:2]
        visibility = np.ones(vis_shape, dtype=np.float32)

    return landmarks, visibility


def render_overlay(video_path: Path, npz_path: Path, out_path: Path):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    landmarks, visibility = load_pose(npz_path)
    num_frames = len(landmarks)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame_idx >= num_frames:
            break

        lm = landmarks[frame_idx]  # (n_points, 3) assumed: x,y,z or x,y,?
        vis = visibility[frame_idx]

        for (i, j) in POSE_CONNECTIONS:
            if i < lm.shape[0] and j < lm.shape[0]:
                if vis[i] > 0.3 and vis[j] > 0.3:
                    x1, y1 = int(lm[i][0] * w), int(lm[i][1] * h)
                    x2, y2 = int(lm[j][0] * w), int(lm[j][1] * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    print(f"[OK] Overlay written to: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Render skeleton overlay video from pose NPZ + raw video."
    )
    parser.add_argument("--exercise", required=True, help="bench/squat/curl/deadlift")
    parser.add_argument("--video", required=True, help="Path to raw video (under data/raw)")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    stem = video_path.stem

    npz_path = Path("data/processed/pose") / args.exercise / f"{stem}.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Pose NPZ not found: {npz_path}")

    out_dir = Path("data/processed/overlays") / args.exercise
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stem}_overlay.mp4"

    print(f"[INFO] Video:   {video_path}")
    print(f"[INFO] Pose:    {npz_path}")
    print(f"[INFO] Overlay: {out_path}")

    render_overlay(video_path, npz_path, out_path)


if __name__ == "__main__":
    main()
