import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

import mediapipe as mp


VALID_EXERCISES = ["bench", "squat", "curl", "deadlift"]


def iter_videos(exercise_root: Path):
    """
    Yield all video files (*.mp4, *.mov, *.avi, *.mkv) under exercise_root.
    """
    exts = {".mp4", ".mov", ".avi", ".mkv"}
    for path in exercise_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            yield path


def extract_pose_from_video(video_path: Path, out_npz: Path, out_meta: Path):
    """
    Run MediaPipe Pose on a single video and save:
      - joint array to .npz
      - basic metadata to .json
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[WARN] Could not open video: {video_path}", file=sys.stderr)
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Pre-allocate: (frames, 33 landmarks, 4 values: x, y, z, visibility)
    n_landmarks = 33
    data = np.full((frame_count, n_landmarks, 4), np.nan, dtype=np.float32)

    mp_pose = mp.solutions.pose

    frame_idx = 0
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                for i, lm in enumerate(results.pose_landmarks.landmark):
                    if i >= n_landmarks:
                        break
                    data[frame_idx, i, 0] = lm.x
                    data[frame_idx, i, 1] = lm.y
                    data[frame_idx, i, 2] = lm.z
                    data[frame_idx, i, 3] = lm.visibility
            # else: row stays as NaN

            frame_idx += 1
            if frame_idx >= frame_count:
                break

    cap.release()

    # In case CAP_PROP_FRAME_COUNT was slightly off:
    data = data[:frame_idx]

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, pose=data)

    meta = {
        "source_video": str(video_path),
        "fps": float(fps) if fps is not None else None,
        "frame_count": int(frame_idx),
        "width": width,
        "height": height,
        "n_landmarks": n_landmarks,
        "mediapipe_version": getattr(mp, "__version__", "unknown"),
    }
    with out_meta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def process_exercise(raw_root: Path, processed_root: Path, exercise: str, max_videos: int | None = None):
    """
    Process all videos for a single exercise.
    """
    in_dir = raw_root / exercise
    out_dir = processed_root / "pose" / exercise

    if not in_dir.exists():
        print(f"[WARN] Raw folder does not exist for {exercise}: {in_dir}", file=sys.stderr)
        return

    videos = list(iter_videos(in_dir))
    if not videos:
        print(f"[WARN] No videos found for {exercise} under {in_dir}", file=sys.stderr)
        return

    if max_videos is not None:
        videos = videos[:max_videos]

    iterator = videos
    if tqdm is not None:
        iterator = tqdm(videos, desc=f"{exercise} videos", unit="video")

    for vid in iterator:
        stem = vid.stem
        out_npz = out_dir / f"{stem}.npz"
        out_meta = out_dir / f"{stem}_meta.json"

        # Skip if we already processed this video
        if out_npz.exists() and out_meta.exists():
            continue

        try:
            extract_pose_from_video(vid, out_npz, out_meta)
        except Exception as e:
            print(f"[ERROR] Failed on {vid}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Extract MediaPipe pose from raw RepRight videos.")
    parser.add_argument(
        "--exercise",
        type=str,
        default="all",
        help="One of bench,squat,curl,deadlift,all (default: all)",
    )
    parser.add_argument(
        "--raw-root",
        type=str,
        default="data/raw",
        help="Root folder containing raw exercise subfolders.",
    )
    parser.add_argument(
        "--processed-root",
        type=str,
        default="data/processed",
        help="Root folder for processed outputs.",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=None,
        help="Optional limit on number of videos per exercise (for testing).",
    )

    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    processed_root = Path(args.processed_root)

    if args.exercise == "all":
        exercises = VALID_EXERCISES
    else:
        ex = args.exercise.lower()
        if ex not in VALID_EXERCISES:
            print(f"Invalid exercise '{args.exercise}'. Must be one of {VALID_EXERCISES} or 'all'.", file=sys.stderr)
            sys.exit(1)
        exercises = [ex]

    for ex in exercises:
        process_exercise(raw_root, processed_root, ex, max_videos=args.max_videos)


if __name__ == "__main__":
    main()
