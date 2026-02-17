import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np

VALID_EXERCISES = ["bench", "squat", "curl", "deadlift"]

# MediaPipe landmark indices
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW,    R_ELBOW    = 13, 14
L_WRIST,    R_WRIST    = 15, 16
L_HIP,      R_HIP      = 23, 24
L_KNEE,     R_KNEE     = 25, 26
L_ANKLE,    R_ANKLE    = 27, 28


def moving_average(x: np.ndarray, window: int = 9) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if window <= 1 or len(x) < 3:
        return x
    window = int(window)
    if window > len(x):
        window = max(3, (len(x) // 2) | 1)
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(x, kernel, mode="same")


def ema(x: np.ndarray, alpha: float = 0.25) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return x
    y = np.empty_like(x)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = alpha * x[i] + (1 - alpha) * y[i - 1]
    return y


def interp_nans(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    valid = ~np.isnan(y)
    if valid.sum() < 5:
        return y
    if not valid.all():
        idx = np.arange(len(y))
        y[~valid] = np.interp(idx[~valid], idx[valid], y[valid])
    return y


def angle_2d(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Angle ABC in degrees per frame, using x,y only."""
    ba = a - b
    bc = c - b
    ba_n = np.linalg.norm(ba, axis=1) + 1e-9
    bc_n = np.linalg.norm(bc, axis=1) + 1e-9
    cosang = np.sum(ba * bc, axis=1) / (ba_n * bc_n)
    cosang = np.clip(cosang, -1.0, 1.0)
    return np.degrees(np.arccos(cosang))


def robust_normalize(x: np.ndarray, lo: float = 5.0, hi: float = 95.0) -> np.ndarray:
    """Normalize ~[0,1] using robust percentiles."""
    x = np.asarray(x, dtype=float)
    if len(x) < 5:
        return np.zeros_like(x)
    p_lo = np.percentile(x, lo)
    p_hi = np.percentile(x, hi)
    denom = (p_hi - p_lo) if (p_hi - p_lo) != 0 else 1.0
    z = (x - p_lo) / denom
    return np.clip(z, 0.0, 1.0)


def robust_amp(x: np.ndarray, lo: float = 5.0, hi: float = 95.0) -> float:
    x = np.asarray(x, dtype=float)
    if len(x) < 5:
        return 0.0
    return float(np.percentile(x, hi) - np.percentile(x, lo))


def pick_side_by_visibility(pose: np.ndarray, idx_l: int, idx_r: int) -> str:
    v_l = np.nanmedian(pose[:, idx_l, 3])
    v_r = np.nanmedian(pose[:, idx_r, 3])
    return "L" if v_l >= v_r else "R"


def build_candidate_signals(pose: np.ndarray, exercise: str) -> Dict[str, np.ndarray]:
    """
    Returns dict: name -> signal (raw, not normalized).
    Signals are oriented so TOP is higher than BOTTOM for counting.
    """
    xy = pose[:, :, 0:2].astype(float)

    cands: Dict[str, np.ndarray] = {}

    # Angles
    elbow_L = angle_2d(xy[:, L_SHOULDER], xy[:, L_ELBOW], xy[:, L_WRIST])
    elbow_R = angle_2d(xy[:, R_SHOULDER], xy[:, R_ELBOW], xy[:, R_WRIST])
    knee_L  = angle_2d(xy[:, L_HIP], xy[:, L_KNEE], xy[:, L_ANKLE])
    knee_R  = angle_2d(xy[:, R_HIP], xy[:, R_KNEE], xy[:, R_ANKLE])

    cands["elbow_angle_L"] = interp_nans(elbow_L)
    cands["elbow_angle_R"] = interp_nans(elbow_R)
    cands["knee_angle_L"]  = interp_nans(knee_L)
    cands["knee_angle_R"]  = interp_nans(knee_R)

    # Vertical proxies (inverted image Y so UP is higher)
    with np.errstate(all="ignore"):
        wrists_y = np.nanmean(pose[:, [L_WRIST, R_WRIST], 1], axis=1)
        hips_y   = np.nanmean(pose[:, [L_HIP, R_HIP], 1], axis=1)

    wrist_L = -interp_nans(pose[:, L_WRIST, 1])
    wrist_R = -interp_nans(pose[:, R_WRIST, 1])
    wrist_M = -interp_nans(wrists_y)

    hip_L = -interp_nans(pose[:, L_HIP, 1])
    hip_R = -interp_nans(pose[:, R_HIP, 1])
    hip_M = -interp_nans(hips_y)

    cands["wrist_y_inverted_L"]    = wrist_L
    cands["wrist_y_inverted_R"]    = wrist_R
    cands["wrist_y_inverted_mean"] = wrist_M

    cands["hip_y_inverted_L"]      = hip_L
    cands["hip_y_inverted_R"]      = hip_R
    cands["hip_y_inverted_mean"]   = hip_M

    # Filter per exercise (keep relevant)
    if exercise in ("bench", "curl"):
        keep = ["elbow_angle_L", "elbow_angle_R", "wrist_y_inverted_L", "wrist_y_inverted_R", "wrist_y_inverted_mean"]
    elif exercise == "squat":
        keep = ["knee_angle_L", "knee_angle_R", "hip_y_inverted_L", "hip_y_inverted_R", "hip_y_inverted_mean"]
    elif exercise == "deadlift":
        keep = ["hip_y_inverted_L", "hip_y_inverted_R", "hip_y_inverted_mean"]
    else:
        keep = list(cands.keys())

    return {k: cands[k] for k in keep if k in cands}


def choose_best_signal(pose: np.ndarray, exercise: str) -> Tuple[np.ndarray, str]:
    """
    Choose the candidate with the largest robust amplitude after smoothing.
    """
    cands = build_candidate_signals(pose, exercise)
    best_name = None
    best_sig = None
    best_amp = -1.0

    for name, sig in cands.items():
        if sig is None or len(sig) < 10:
            continue
        sig = np.asarray(sig, float)
        nan_pct = float(np.mean(np.isnan(sig)) * 100.0)
        if nan_pct > 60.0:
            continue

        sm = ema(moving_average(sig, 9), 0.25)
        amp = robust_amp(sm)
        if amp > best_amp:
            best_amp = amp
            best_name = name
            best_sig = sig

    if best_sig is None:
        # fallback to something deterministic
        return cands[list(cands.keys())[0]], list(cands.keys())[0]

    return best_sig, best_name


def per_exercise_params(ex: str) -> Tuple[float, float, float]:
    """
    Returns (low, high, min_rep_sec).
    low/high are in normalized [0,1] space.
    """
    if ex == "curl":
        return 0.25, 0.70, 0.50
    if ex == "bench":
        return 0.25, 0.75, 0.70
    if ex == "squat":
        return 0.25, 0.75, 0.80
    if ex == "deadlift":
        return 0.25, 0.75, 1.00
    return 0.25, 0.75, 0.80


def detect_reps_low_to_high(
    signal: np.ndarray,
    fps: float,
    low: float,
    high: float,
    min_rep_sec: float,
) -> List[Tuple[int, int, int]]:
    """
    Count reps on LOW -> HIGH transitions (hysteresis).
    This fixes the "hit LOW only before first HIGH" / "clip ends before returning LOW" problem.

    Returns list of (start_idx, peak_idx, end_idx)
      start_idx = last frame at/below LOW before the ascent
      peak_idx  = first frame at/above HIGH (rep counted here)
      end_idx   = next LOW if found, else = peak_idx (partial cycle)
    """
    if len(signal) < 10 or fps <= 0:
        return []

    s_raw = np.asarray(signal, float)
    s_sm = ema(moving_average(s_raw, 9), 0.25)
    s = robust_normalize(s_sm)

    min_frames = max(1, int(min_rep_sec * fps))

    reps: List[Tuple[int, int, int]] = []
    last_count_i = -10**9

    # track whether we've been at/below low since last count
    in_low = bool(s[0] <= low)
    last_low_i = 0 if in_low else None

    n = len(s)
    for i in range(n):
        v = s[i]

        if v <= low:
            in_low = True
            last_low_i = i

        # count when we climb from a confirmed low into high
        if in_low and v >= high and (i - last_count_i) >= min_frames and last_low_i is not None:
            start = int(last_low_i)
            peak = int(i)

            # try to find next return to low for end_idx (for duration/tempo)
            j = i
            while j < n and s[j] > low:
                j += 1
            end = int(j) if j < n else peak

            reps.append((start, peak, end))
            last_count_i = i
            in_low = False  # must return to low before next rep

    return reps


def compute_rep_metrics(signal: np.ndarray, reps: List[Tuple[int, int, int]], fps: float) -> List[Dict]:
    if fps <= 0:
        fps = 30.0

    metrics: List[Dict] = []
    for idx, (start, peak, end) in enumerate(reps, start=1):
        start = int(start); peak = int(peak); end = int(end)
        if peak < start:
            continue
        if end < peak:
            end = peak

        seg = np.asarray(signal[start:end + 1], float)
        rom = float(np.nanmax(seg) - np.nanmin(seg)) if len(seg) else 0.0

        duration_frames = (end - start + 1)
        up_frames = max(0, peak - start)
        down_frames = max(0, end - peak)

        metrics.append({
            "rep_index": idx,
            "start_frame": start,
            "peak_frame": peak,
            "end_frame": end,
            "rom": rom,
            "duration_sec": float(duration_frames / fps),
            "tempo_up_sec": float(up_frames / fps),
            "tempo_down_sec": float(down_frames / fps),
        })

    return metrics


def process_exercise(exercise: str, processed_root: Path, max_videos: Optional[int], force: bool):
    pose_dir = processed_root / "pose" / exercise
    metrics_dir = processed_root / "metrics" / exercise
    metrics_dir.mkdir(parents=True, exist_ok=True)

    npz_files = sorted(pose_dir.glob("*.npz"))
    if not npz_files:
        print(f"[WARN] No NPZ pose files for {exercise} under {pose_dir}")
        return

    if max_videos is not None:
        npz_files = npz_files[:max_videos]

    low, high, min_rep_sec = per_exercise_params(exercise)

    for npz_path in npz_files:
        stem = npz_path.stem
        meta_path = pose_dir / f"{stem}_meta.json"
        out_path = metrics_dir / f"{stem}_metrics.json"

        if out_path.exists() and not force:
            continue

        pose = np.load(npz_path)["pose"]

        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            fps = float(meta.get("fps", 30.0) or 30.0)
        else:
            fps = 30.0

        sig, driver = choose_best_signal(pose, exercise)
        sig = np.asarray(sig, float)

        if len(sig) < 10 or np.all(np.isnan(sig)):
            print(f"[WARN] Bad signal for {exercise} {npz_path.name}")
            continue

        reps = detect_reps_low_to_high(sig, fps=fps, low=low, high=high, min_rep_sec=min_rep_sec)
        rep_metrics = compute_rep_metrics(sig, reps, fps)

        summary = {
            "exercise": exercise,
            "driver": driver,
            "source_npz": str(npz_path),
            "source_meta": str(meta_path) if meta_path.exists() else None,
            "fps": fps,
            "n_frames": int(pose.shape[0]),
            "n_reps": len(rep_metrics),
            "reps": rep_metrics,
        }

        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"[OK] {exercise}: {stem} \u2192 {len(rep_metrics)} reps (driver={driver})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", type=str, default="all")
    ap.add_argument("--processed-root", type=str, default="data/processed")
    ap.add_argument("--max-videos", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="Overwrite existing metrics JSONs")
    args = ap.parse_args()

    processed_root = Path(args.processed_root)

    if args.exercise == "all":
        exercises = VALID_EXERCISES
    else:
        ex = args.exercise.lower().strip()
        if ex not in VALID_EXERCISES:
            raise SystemExit(f"Invalid exercise {args.exercise}. Must be one of {VALID_EXERCISES} or 'all'.")
        exercises = [ex]

    for ex in exercises:
        process_exercise(ex, processed_root, args.max_videos, args.force)


if __name__ == "__main__":
    main()
