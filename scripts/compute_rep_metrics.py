import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


VALID_EXERCISES = ["bench", "squat", "curl", "deadlift"]


def moving_average(x: np.ndarray, window: int = 5) -> np.ndarray:
    if window <= 1:
        return x
    if window > len(x):
        window = max(1, len(x) // 2)
        if window <= 1:
            return x
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(x, kernel, mode="same")


def build_signal(pose: np.ndarray, exercise: str) -> np.ndarray:
    """
    Build a 1-D vertical motion signal per exercise from pose array:
      pose: (T, 33, 4)  [x,y,z,visibility] in image coordinates
    We invert Y so 'up' = larger value.
    """
    # y indices
    L_WRIST, R_WRIST = 15, 16
    L_HIP,   R_HIP   = 23, 24

    y = None

    if exercise == "bench":
        # Bench: bar path ~ wrist vertical
        wrists = pose[:, [L_WRIST, R_WRIST], 1]
        y = np.nanmean(wrists, axis=1)
    elif exercise == "curl":
        # Curl: wrist vertical (works for hammer & biceps curl)
        wrists = pose[:, [L_WRIST, R_WRIST], 1]
        y = np.nanmean(wrists, axis=1)
    elif exercise in ("squat", "deadlift"):
        # Squat + deadlift: hip vertical
        hips = pose[:, [L_HIP, R_HIP], 1]
        y = np.nanmean(hips, axis=1)
    else:
        raise ValueError(f"Unknown exercise {exercise}")

    # Some frames might be NaN if pose failed → simple interpolation
    y = np.asarray(y, dtype=float)
    valid = ~np.isnan(y)
    if valid.sum() < 5:
        return y  # not enough data

    if not valid.all():
        idx = np.arange(len(y))
        y[~valid] = np.interp(idx[~valid], idx[valid], y[valid])

    # Invert Y (image coords: top=0, bottom=1) so that UP is positive
    signal = -y
    return signal


def detect_reps(signal: np.ndarray,
                min_prominence: float = 0.02,
                min_distance: int = 10) -> List[Tuple[int, int, int]]:
    """
    Super simple peak-based rep detector.
    Returns list of (start_idx, peak_idx, end_idx) for each rep.
    """
    if len(signal) < 5:
        return []

    s = moving_average(signal, window=7)

    s_min = float(np.min(s))
    s_max = float(np.max(s))
    amplitude = s_max - s_min
    if amplitude <= 0:
        return []

    threshold = s_min + min_prominence * amplitude

    peaks = []
    last_peak = -min_distance

    for i in range(1, len(s) - 1):
        if s[i] > s[i - 1] and s[i] > s[i + 1] and s[i] > threshold:
            if i - last_peak >= min_distance:
                peaks.append(i)
                last_peak = i

    reps: List[Tuple[int, int, int]] = []

    for peak in peaks:
        # find local minima before and after peak
        start = peak
        while start > 1 and s[start - 1] <= s[start]:
            start -= 1

        end = peak
        while end < len(s) - 2 and s[end + 1] <= s[end]:
            end += 1

        if end - start < 3:
            continue

        reps.append((start, peak, end))

    return reps


def compute_rep_metrics(
    signal: np.ndarray,
    reps: List[Tuple[int, int, int]],
    fps: float
) -> List[Dict]:
    metrics = []
    for idx, (start, peak, end) in enumerate(reps, start=1):
        seg = signal[start:end + 1]
        bottom_val = float(min(seg[0], seg[-1]))
        top_val = float(signal[peak])

        rom = top_val - bottom_val  # relative ROM (in signal units)

        duration_frames = end - start + 1
        up_frames = max(0, peak - start)
        down_frames = max(0, end - peak)

        duration_sec = float(duration_frames / fps) if fps and fps > 0 else None
        up_sec = float(up_frames / fps) if fps and fps > 0 else None
        down_sec = float(down_frames / fps) if fps and fps > 0 else None

        metrics.append(
            {
                "rep_index": idx,
                "start_frame": int(start),
                "peak_frame": int(peak),
                "end_frame": int(end),
                "rom": rom,
                "duration_sec": duration_sec,
                "tempo_up_sec": up_sec,
                "tempo_down_sec": down_sec,
            }
        )

    return metrics


def process_exercise(exercise: str,
                     processed_root: Path,
                     max_videos: int | None = None):
    pose_dir = processed_root / "pose" / exercise
    metrics_dir = processed_root / "metrics" / exercise
    metrics_dir.mkdir(parents=True, exist_ok=True)

    npz_files = sorted(pose_dir.glob("*.npz"))
    if not npz_files:
        print(f"[WARN] No NPZ pose files for {exercise} under {pose_dir}")
        return

    if max_videos is not None:
        npz_files = npz_files[:max_videos]

    for npz_path in npz_files:
        stem = npz_path.stem
        meta_path = pose_dir / f"{stem}_meta.json"
        out_path = metrics_dir / f"{stem}_metrics.json"

        if out_path.exists():
            # skip already computed
            continue

        pose_data = np.load(npz_path)["pose"]  # (T, 33, 4)

        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            fps = float(meta.get("fps", 30.0) or 30.0)
        else:
            fps = 30.0
            meta = {"fps": fps}

        signal = build_signal(pose_data, exercise)
        if np.all(np.isnan(signal)):
            print(f"[WARN] All-NaN signal for {exercise} {npz_path.name}")
            continue

        reps = detect_reps(signal)
        rep_metrics = compute_rep_metrics(signal, reps, fps)

        summary = {
            "exercise": exercise,
            "source_npz": str(npz_path),
            "source_meta": str(meta_path) if meta_path.exists() else None,
            "fps": fps,
            "n_frames": int(pose_data.shape[0]),
            "n_reps": len(rep_metrics),
            "reps": rep_metrics,
        }

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"[OK] {exercise}: {stem} → {len(rep_metrics)} reps")


def main():
    parser = argparse.ArgumentParser(description="Compute simple rep metrics from pose NPZ files.")
    parser.add_argument(
        "--exercise",
        type=str,
        default="all",
        help="One of bench,squat,curl,deadlift,all (default: all)",
    )
    parser.add_argument(
        "--processed-root",
        type=str,
        default="data/processed",
        help="Root folder that contains pose/ and metrics/ subfolders.",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=None,
        help="Optional limit on number of videos per exercise for testing.",
    )

    args = parser.parse_args()

    processed_root = Path(args.processed_root)

    if args.exercise == "all":
        exercises = VALID_EXERCISES
    else:
        ex = args.exercise.lower()
        if ex not in VALID_EXERCISES:
            raise SystemExit(f"Invalid exercise {args.exercise}. Must be one of {VALID_EXERCISES} or 'all'.")
        exercises = [ex]

    for ex in exercises:
        process_exercise(ex, processed_root, max_videos=args.max_videos)


if __name__ == "__main__":
    main()
