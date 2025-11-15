import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, find_peaks

VIDEO_EXTS = {'.mp4','.mov','.m4v','.avi','.webm','.mkv'}

def load_series(jsonl_path: Path):
    t, ang = [], []
    with jsonl_path.open('r', encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
                a = row.get('angles', {}).get('driver', None)
                tt = row.get('t', None)
                if a is not None and tt is not None:
                    t.append(float(tt)); ang.append(float(a))
            except Exception:
                pass
    return np.array(t), np.array(ang)

def pick_window(n: int, fps: float):
    if n < 7:
        return max(3, n - (1 - n % 2))  # smallest odd
    base = max(5, int(round(0.21 * fps)))   # ~0.2s window
    if base % 2 == 0: base += 1
    base = min(base, n - 1 if (n - 1) % 2 == 1 else n - 2)
    return max(5, base)

def smooth_and_deriv(t, ang, fps):
    if len(ang) < 5:
        return ang.copy(), np.zeros_like(ang)
    w = pick_window(len(ang), fps)
    poly = 3 if w >= 7 else (2 if w >= 5 else 1)
    s = savgol_filter(ang, window_length=w, polyorder=poly, mode='interp')
    # robust gradient on uneven dt
    dt = np.gradient(t)
    dt[dt == 0] = np.median(dt[dt > 0]) if np.any(dt > 0) else 1.0 / max(fps, 1.0)
    v = np.gradient(s) / dt
    return s, v

def detect_reps(label: str, t, s, fps):
    """
    Rep = top -> bottom -> top (extension peak to flexion trough to extension peak).
    Works for bench/curl/squat with driver angles we chose.
    """
    if len(s) < 7:
        return []

    prom = 12.0  # deg
    dist = max(3, int(0.25 * fps))  # >= ~0.25s between peaks

    hi_idx, _ = find_peaks(s, prominence=prom, distance=dist)
    lo_idx, _ = find_peaks(-s, prominence=prom, distance=dist)

    # merge extremes by time
    extremes = [(i, 'hi') for i in hi_idx] + [(i, 'lo') for i in lo_idx]
    extremes.sort(key=lambda x: x[0])

    reps = []
    prev_hi = None
    pending_lo = None
    for i, typ in extremes:
        if typ == 'hi':
            if prev_hi is None:
                prev_hi = i
            elif pending_lo is not None:
                # complete cycle: hi -> lo -> hi
                top1, bot, top2 = prev_hi, pending_lo, i
                if top1 < bot < top2:
                    ecc = float(t[bot] - t[top1])
                    con = float(t[top2] - t[bot])
                    rom = float(abs(s[top1] - s[bot]))
                    tut = ecc + con
                    reps.append({
                        "t_start": float(t[top1]),
                        "t_mid": float(t[bot]),
                        "t_end": float(t[top2]),
                        "ecc_s": round(ecc, 3),
                        "con_s": round(con, 3),
                        "tut_s": round(tut, 3),
                        "rom_deg": round(rom, 1),
                    })
                # shift window to new cycle
                prev_hi = i
                pending_lo = None
            else:
                # hi came but no lo yet -> update top marker
                prev_hi = i
        else:  # lo
            if prev_hi is not None:
                pending_lo = i
            # else lo before any hi -> ignore
    return reps

def process_one(jsonl_path: Path, out_dir: Path):
    label = jsonl_path.parent.name  # processed/<label>/
    # read fps from sibling _summary.json
    stem = jsonl_path.stem  # original video name
    summary_path = jsonl_path.with_name(f"{stem}_summary.json")
    fps = 25.0
    try:
        js = json.loads(summary_path.read_text(encoding='utf-8'))
        fps = float(js.get('fps', 25.0))
    except Exception:
        pass

    t, ang = load_series(jsonl_path)
    if len(t) == 0:
        return None

    s, v = smooth_and_deriv(t, ang, fps)
    reps = detect_reps(label, t, s, fps)

    # write per-video CSV
    vid_out_dir = out_dir / "reps" / label
    vid_out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = vid_out_dir / f"{stem}_reps.csv"
    df = pd.DataFrame(reps)
    if len(df) == 0:
        # still write empty to mark attempted
        df = pd.DataFrame(columns=["t_start","t_mid","t_end","ecc_s","con_s","tut_s","rom_deg"])
    df.to_csv(csv_path, index=False)

    # aggregate set-level metrics
    agg = {
        "video": stem,
        "label": label,
        "fps": fps,
        "frames": int(js.get("frames", 0)) if 'js' in locals() else None,
        "duration_s": float(js.get("duration_s", float(t[-1]) if len(t) else 0.0)) if 'js' in locals() else (float(t[-1]) if len(t) else 0.0),
        "reps": int(len(reps)),
        "avg_rom_deg": float(np.mean([r["rom_deg"] for r in reps])) if reps else 0.0,
        "avg_tut_s": float(np.mean([r["tut_s"] for r in reps])) if reps else 0.0,
        "avg_ecc_s": float(np.mean([r["ecc_s"] for r in reps])) if reps else 0.0,
        "avg_con_s": float(np.mean([r["con_s"] for r in reps])) if reps else 0.0,
    }
    return agg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="in_dir",  required=True, help="processed root (e.g., data/processed)")
    ap.add_argument("--out", dest="out_dir", required=True, help="reports root (e.g., data/reports)")
    args = ap.parse_args()

    in_root  = Path(args.in_dir)
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    jsonls = list(in_root.rglob("*.jsonl"))
    aggs = []
    for jp in jsonls:
        agg = process_one(jp, out_root)
        if agg:
            aggs.append(agg)

    # write combined tables
    sets_csv = out_root / "sets_all.csv"
    pd.DataFrame(aggs).to_csv(sets_csv, index=False)

if __name__ == "__main__":
    main()
