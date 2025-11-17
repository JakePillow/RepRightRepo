import argparse, json, csv
from pathlib import Path
from statistics import mean

def load_series(jsonl_path: Path):
    frames = []
    angles = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            frame = row.get("frame")
            a = None
            angles_dict = row.get("angles") or {}
            if isinstance(angles_dict, dict):
                a = angles_dict.get("driver")
            if a is None:
                continue
            try:
                a = float(a)
            except (TypeError, ValueError):
                continue
            frames.append(int(frame))
            angles.append(a)
    return frames, angles

def smooth_angles(angles, win=5):
    if not angles:
        return []
    out = []
    n = len(angles)
    half = win // 2
    for i in range(n):
        s = 0.0
        c = 0
        for j in range(max(0, i - half), min(n, i + half + 1)):
            s += angles[j]
            c += 1
        out.append(s / c)
    return out

def detect_reps(frames, angles_smooth, fps, label):
    """
    Lenient rep detection:
      - Use dynamic thresholds based on per-video ROM.
      - Count any clear down->up->down cycle as a rep.
    """
    if len(angles_smooth) < 5:
        return []

    a_min = min(angles_smooth)
    a_max = max(angles_smooth)
    rom_total = a_max - a_min

    # If the joint barely moves, treat as no reps
    if rom_total < 20.0:
        return []

    # Dynamic thresholds: top / bottom 25% of that video's range
    down_thr = a_max - 0.25 * rom_total
    up_thr   = a_min + 0.25 * rom_total

    reps = []
    state = "down"  # start assuming arm is near extended
    rep_start_idx = None

    prev_a = angles_smooth[0]
    prev_f = frames[0]

    for i in range(1, len(angles_smooth)):
        a = angles_smooth[i]
        f = frames[i]

        if state in ("init", "down"):
            # Look for transition into "up" (curling / concentric)
            if prev_a > up_thr and a <= up_thr:
                state = "up"
                rep_start_idx = i

        elif state == "up":
            # Look for return to "down" (eccentric back to start)
            if prev_a < down_thr and a >= down_thr and rep_start_idx is not None:
                rep_end_idx = i

                start_f = frames[rep_start_idx]
                end_f = frames[rep_end_idx]
                dur_s = (end_f - start_f) / float(fps or 25.0)

                # Reject ultra-quick jitters
                if dur_s >= 0.25:
                    seg = angles_smooth[rep_start_idx:rep_end_idx+1]
                    seg_min = min(seg)
                    seg_max = max(seg)
                    seg_rom = seg_max - seg_min

                    # Require the rep to use at least 30% of that person's ROM
                    if seg_rom >= 0.30 * rom_total:
                        reps.append({
                            "start_frame": int(start_f),
                            "end_frame": int(end_f),
                            "duration_s": float(dur_s),
                            "rom_deg": float(seg_rom),
                        })

                # Ready for next rep
                state = "down"
                rep_start_idx = None

        prev_a = a
        prev_f = f

    return reps

def is_good_rep(rep, label):
    rom = rep.get("rom_deg", 0.0)
    dur = rep.get("duration_s", 0.0)

    if label == "curl":
        rom_ok = rom >= 60.0      # big elbow flexion
        dur_ok = 0.6 <= dur <= 8.0
    elif label == "bench":
        rom_ok = rom >= 40.0
        dur_ok = 0.6 <= dur <= 8.0
    elif label == "squat":
        rom_ok = rom >= 50.0
        dur_ok = 0.8 <= dur <= 8.0
    else:
        rom_ok = rom >= 30.0
        dur_ok = 0.4 <= dur <= 8.0

    return rom_ok and dur_ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, help="processed root (e.g. data/processed)")
    ap.add_argument("--out", dest="out_dir", required=True, help="reports root (e.g. data/reports)")
    args = ap.parse_args()

    in_root = Path(args.in_dir)
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # We'll drive off the *_summary.json files
    summaries = sorted(in_root.rglob("*_summary.json"))

    csv_path = out_root / "sets_all.csv"
    fieldnames = [
        "video", "label", "fps", "frames", "duration_s",
        "reps", "avg_tut_s", "avg_rom_deg", "good_rep_pct"
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()

        for summary_path in summaries:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            label = summary.get("label", "unknown")
            fps = float(summary.get("fps", 25.0))
            frames_total = int(summary.get("frames", 0))
            duration_s = float(summary.get("duration_s", 0.0))

            stem = summary_path.stem.replace("_summary", "")
            jsonl_path = summary_path.with_name(stem + ".jsonl")
            if not jsonl_path.exists():
                # No per-frame data; skip
                row = {
                    "video": stem,
                    "label": label,
                    "fps": fps,
                    "frames": frames_total,
                    "duration_s": duration_s,
                    "reps": 0,
                    "avg_tut_s": 0.0,
                    "avg_rom_deg": 0.0,
                    "good_rep_pct": 0.0,
                }
                writer.writerow(row)
                continue

            frames, angles = load_series(jsonl_path)
            if not frames or not angles:
                # Nothing usable; write zeros
                row = {
                    "video": stem,
                    "label": label,
                    "fps": fps,
                    "frames": frames_total,
                    "duration_s": duration_s,
                    "reps": 0,
                    "avg_tut_s": 0.0,
                    "avg_rom_deg": 0.0,
                    "good_rep_pct": 0.0,
                }
                writer.writerow(row)
                continue

            angles_smooth = smooth_angles(angles, win=5)
            reps = detect_reps(frames, angles_smooth, fps, label)

            # Save per-rep details for later analysis if needed
            reps_out = []
            good_flags = []
            for rep in reps:
                good = is_good_rep(rep, label)
                rep_rec = dict(rep)
                rep_rec["good_rep"] = bool(good)
                reps_out.append(rep_rec)
                good_flags.append(good)

            if reps_out:
                reps_path = summary_path.with_name(stem + "_reps.json")
                reps_path.write_text(json.dumps(reps_out, indent=2), encoding="utf-8")

            if reps:
                avg_tut = mean(r["duration_s"] for r in reps)
                avg_rom = mean(r["rom_deg"] for r in reps)
                good_pct = (sum(1 for g in good_flags if g) / len(good_flags)) if good_flags else 0.0
            else:
                avg_tut = 0.0
                avg_rom = 0.0
                good_pct = 0.0

            row = {
                "video": stem,
                "label": label,
                "fps": fps,
                "frames": frames_total,
                "duration_s": duration_s,
                "reps": len(reps),
                "avg_tut_s": round(avg_tut, 3),
                "avg_rom_deg": round(avg_rom, 1),
                "good_rep_pct": round(good_pct * 100.0, 1),
            }
            writer.writerow(row)

if __name__ == "__main__":
    main()
