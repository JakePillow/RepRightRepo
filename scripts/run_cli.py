import argparse
import os
import math

from engine import analyze_video


JOINT_LABELS = {
    "bench": "elbow",
    "curl": "elbow",
    "squat": "knee",
    "deadlift": "hip",
}


def _fmt_bool(b):
    return "True" if bool(b) else "False"


def main():
    parser = argparse.ArgumentParser(
        description="RepRight CLI – analyse a single exercise video"
    )
    parser.add_argument(
        "video",
        type=str,
        help="Path to the raw video file (e.g. data/raw/curl/barbell biceps curl_41.mp4)",
    )
    parser.add_argument(
        "--exercise",
        type=str,
        required=True,
        choices=["bench", "curl", "squat", "deadlift"],
        help="Exercise type",
    )

    args = parser.parse_args()
    video_path = args.video
    exercise = args.exercise.lower()

    result = analyze_video(video_path, exercise)

    # Basic fields
    valid = result.get("valid", True)
    difficulty = result.get("difficulty", "unknown")
    n_reps = result.get("n_reps", result.get("reps", 0))

    avg_rom = result.get("avg_rom", float("nan"))
    avg_dur = result.get("avg_duration_sec", float("nan"))

    # Angle ROM (per-joint) if present
    angle_rom = result.get("avg_angle_rom", {})
    joint_key = JOINT_LABELS.get(exercise)
    joint_angle = None
    if isinstance(angle_rom, dict) and joint_key in angle_rom:
        val = angle_rom.get(joint_key)
        if isinstance(val, (int, float)) and not math.isnan(val):
            joint_angle = float(val)

    # Header
    print()
    print("=== RepRight Analysis ===")
    print(f"Exercise:   {exercise}")
    print(f"Video:      {video_path}")
    print(f"Valid:      {_fmt_bool(valid)}")
    print(f"Difficulty: {difficulty}")

    if isinstance(n_reps, (int, float)):
        print(f"Reps:       {int(n_reps)}")
    else:
        print("Reps:       n/a")

    if isinstance(avg_rom, (int, float)) and not math.isnan(avg_rom):
        print(f"Avg ROM:    {avg_rom:.3f}")
    else:
        print("Avg ROM:    n/a")

    if isinstance(avg_dur, (int, float)) and not math.isnan(avg_dur):
        print(f"Avg dur:    {avg_dur:.2f} s")
    else:
        print("Avg dur:    n/a")

    if joint_angle is not None and joint_key is not None:
        # e.g. "Avg elbow ROM: 56.7°"
        print(f"Avg {joint_key} ROM: {joint_angle:.1f}°")

    # High-level summary
    print()
    print(f"Overall: Detected {int(n_reps) if isinstance(n_reps, (int, float)) else 'n/a'} reps for {exercise}.")

    # Per-rep feedback (if available)
        # Per-rep feedback (engine returns `per_rep`)
    per_rep = result.get("per_rep")
    if isinstance(per_rep, list) and per_rep:
        print()
        print("Per-rep feedback:")
        for rep in per_rep:
            idx = rep.get("rep_index", "?")
            analysis = (rep.get("analysis") or {})
            msg = analysis.get("message", "")
            quality = analysis.get("quality", "unknown")
            print(f"  Rep {idx}: [{quality}] {msg}")

    # Load / rep range suggestions (if present)
    load_suggestion = result.get("load_suggestion")
    rep_range_suggestion = result.get("rep_range_suggestion")

    if load_suggestion:
        print()
        print(f"Load Suggestion: {load_suggestion}")

    if rep_range_suggestion:
        print(f"Rep Range Suggestion: {rep_range_suggestion}")


if __name__ == "__main__":
    main()

