import argparse, json, math, shutil, subprocess, time
from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp

VIDEO_EXTS = {'.mp4', '.mov', '.m4v', '.avi', '.webm', '.mkv'}

TOKENS = {
    'bench': ['benchpress', 'bench_press', 'bench', 'barbell_bench', 'dumbbell_bench', 'incline', 'decline'],
    'squat': ['squat', 'back_squat', 'front_squat', 'goblet'],
    'curl':  ['bicep', 'biceps', 'curl', 'barbell_curl', 'ezbar'],
    'deadlift': ['deadlift', 'romanian_deadlift', 'rdl', 'sumo_deadlift'],
}

def guess_label(name: str):
    s = name.lower()
    for label, toks in TOKENS.items():
        for t in toks:
            if t in s:
                return label
    return None

def angle(a, b, c):
    """Angle ABC (in degrees). a,b,c are (x,y) in image space."""
    a = np.array(a, dtype=float); b = np.array(b, dtype=float); c = np.array(c, dtype=float)
    ba = a - b; bc = c - b
    nba = ba / (np.linalg.norm(ba) + 1e-6)
    nbc = bc / (np.linalg.norm(bc) + 1e-6)
    cosang = np.clip(np.dot(nba, nbc), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))

def choose_driver(label, lm):
    """Return a driver angle per exercise for live rep counting."""
    li = mp.solutions.pose.PoseLandmark

    def pt(idx):
        p = lm[idx]
        return (p.x, p.y)

    if label == 'curl':
        return angle(pt(li.RIGHT_SHOULDER), pt(li.RIGHT_ELBOW), pt(li.RIGHT_WRIST))
    elif label == 'bench':
        return angle(pt(li.RIGHT_SHOULDER), pt(li.RIGHT_ELBOW), pt(li.RIGHT_WRIST))
    elif label == 'squat':
        return angle(pt(li.RIGHT_HIP), pt(li.RIGHT_KNEE), pt(li.RIGHT_ANKLE))
    else:
        return angle(pt(li.RIGHT_SHOULDER), pt(li.RIGHT_HIP), pt(li.RIGHT_KNEE))

class LiveRepCounter:
    """
    Very lightweight streaming rep counter on a single driver angle.
    Logic:
      - Maintain direction (descending vs ascending angle).
      - When direction flips and swing >= min_rom and min_phase_frames satisfied -> +1 rep.
    """
    def __init__(self, fps, label):
        self.fps = max(1.0, float(fps))
        self.label = label

        if label == 'curl':
            self.min_rom = 35.0
        elif label == 'squat':
            self.min_rom = 40.0
        else:
            self.min_rom = 30.0

        self.min_phase_frames = int(0.20 * self.fps)  # >=0.2s per half phase

        self.prev = None
        self.dir = 0  # -1 down, +1 up
        self.extreme = None
        self.extreme_frame = 0
        self.frames_since_flip = 0
        self.reps = 0

        self._phase_start_frame = 0
        self._last_flip_frame = 0

    def update(self, frame_idx, driver_angle):
        if self.prev is None:
            self.prev = driver_angle
            self.extreme = driver_angle
            self._phase_start_frame = frame_idx
            return None

        delta = driver_angle - self.prev
        cur_dir = 1 if delta > 0 else (-1 if delta < 0 else self.dir)
        if self.dir == 0:
            self.dir = cur_dir

        if (self.dir > 0 and driver_angle > self.extreme) or (self.dir < 0 and driver_angle < self.extreme):
            self.extreme = driver_angle
            self.extreme_frame = frame_idx

        flipped = (cur_dir != 0 and self.dir != 0 and cur_dir != self.dir)
        self.frames_since_flip += 1

        event = None
        if flipped and self.frames_since_flip >= self.min_phase_frames:
            swing = abs(driver_angle - self.extreme)
            if swing >= self.min_rom:
                self.reps += 1
                event = {"type": "rep", "frame": frame_idx, "reps": self.reps, "rom": float(swing)}
                self._last_flip_frame = frame_idx

            self.dir = cur_dir
            self.extreme = driver_angle
            self.extreme_frame = frame_idx
            self.frames_since_flip = 0

        self.prev = driver_angle
        return event

MIN_VALID_OVERLAY_BYTES = 50 * 1024

def _valid_video_file(path: Path, min_bytes: int = MIN_VALID_OVERLAY_BYTES) -> bool:
    if not path.exists() or path.stat().st_size < min_bytes:
        return False
    cap = cv2.VideoCapture(str(path))
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        return frame_count > 0
    finally:
        cap.release()

def _transcode_with_ffmpeg(src: Path, dst: Path, args: list[str]) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    cmd = [ffmpeg, "-y", "-i", str(src), *args, str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[warn] ffmpeg transcode failed for {dst.name}: {proc.stderr.strip()[:200]}")
        return False
    return _valid_video_file(dst)

def _read_offline_rep_count(analysis_json_path: Path | None) -> int | None:
    """
    If analysis_v1.json exists, use its set_summary_v1.n_reps (or len(reps)) as the HUD count.
    Returns None if not available/readable.
    """
    if analysis_json_path is None:
        return None
    try:
        p = Path(analysis_json_path)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        ss = data.get("set_summary_v1") if isinstance(data.get("set_summary_v1"), dict) else {}
        n = ss.get("n_reps")
        if isinstance(n, int):
            return n
        reps = data.get("reps")
        if isinstance(reps, list):
            return len(reps)
        return None
    except Exception:
        return None

def process_video(
    in_path: Path,
    out_dir: Path,
    label_override: str | None = None,
    analysis_json_path: Path | None = None,
):
    label = (label_override or guess_label(in_path.name) or "bench").lower()
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(in_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    raw_overlay_mp4 = out_dir / f"{in_path.stem}_overlay_raw.mp4"
    overlay_mp4 = out_dir / f"{in_path.stem}_overlay.mp4"
    overlay_webm = out_dir / f"{in_path.stem}_overlay.webm"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(raw_overlay_mp4), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {raw_overlay_mp4}")

    jsonl = (out_dir / f"{in_path.stem}.jsonl").open("w", encoding="utf-8")
    summary_path = out_dir / f"{in_path.stem}_summary.json"

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    draw = mp.solutions.drawing_utils
    style = mp.solutions.drawing_styles

    counter = LiveRepCounter(fps, label)
    frame_idx = 0
    rep_events = []

    t0 = time.time()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)

            angles = {}
            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                drv = choose_driver(label, lm)
                angles["driver"] = drv
                evt = counter.update(frame_idx, drv)
                if evt:
                    rep_events.append(evt)

                draw.draw_landmarks(
                    frame,
                    res.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=style.get_default_pose_landmarks_style()
                )

            # ---- HUD ----
            # Prefer offline (analysis_v1) rep count if available, else live.
            offline_n = _read_offline_rep_count(analysis_json_path)
            hud_reps = offline_n if isinstance(offline_n, int) else counter.reps

            cv2.rectangle(frame, (10, 10), (260, 95), (0, 0, 0), -1)
            cv2.putText(frame, f"{label.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"Reps: {hud_reps}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # write per-frame JSONL
            row = {
                "frame": frame_idx,
                "t": float(frame_idx / (fps or 25.0)),
                "angles": angles,
                "reps": int(hud_reps),
            }
            jsonl.write(json.dumps(row) + "\n")

            writer.write(frame)
            frame_idx += 1

    finally:
        cap.release()
        writer.release()
        jsonl.close()
        pose.close()

    # ---- transcode / final overlay selection ----
    final_overlay = None
    h264_ok = _transcode_with_ffmpeg(
        raw_overlay_mp4,
        overlay_mp4,
        ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    )
    if h264_ok:
        final_overlay = overlay_mp4
    else:
        if _transcode_with_ffmpeg(raw_overlay_mp4, overlay_webm, ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32"]):
            final_overlay = overlay_webm
        elif _valid_video_file(raw_overlay_mp4):
            raw_overlay_mp4.replace(overlay_mp4)
            final_overlay = overlay_mp4

    if raw_overlay_mp4.exists() and final_overlay != raw_overlay_mp4:
        raw_overlay_mp4.unlink(missing_ok=True)

    if not final_overlay or not _valid_video_file(final_overlay):
        print(f"[warn] Overlay output invalid for {in_path.name}; expected > {MIN_VALID_OVERLAY_BYTES} bytes and readable video.")

    dt = time.time() - t0

    # build basic per-set summary
    if frame_idx > 0:
        avg_rep_time = (frame_idx / (fps or 25.0)) / max(1, counter.reps)
    else:
        avg_rep_time = 0.0
    avg_rom = float(np.mean([e.get("rom", 0.0) for e in rep_events])) if rep_events else 0.0

    summary = {
        "video": str(in_path),
        "label": label,
        "frames": int(frame_idx),
        "fps": float(fps),
        "duration_s": float(frame_idx / (fps or 25.0)),
        "reps_live": int(counter.reps),
        "reps_offline": _read_offline_rep_count(analysis_json_path),
        "avg_rep_time_s": round(avg_rep_time, 3),
        "avg_rom_deg": round(avg_rom, 1),
        "overlay_path": str(final_overlay.resolve()) if final_overlay and final_overlay.exists() else None,
        "seconds": round(dt, 3),
        "notes": "Overlay HUD prefers offline rep count (analysis_v1) when available; falls back to streaming counter."
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, help="shortlist root (e.g., data/shortlist)")
    ap.add_argument("--out", dest="out_dir", required=True, help="processed root (e.g., data/processed)")
    args = ap.parse_args()

    in_root = Path(args.in_dir)
    out_root = Path(args.out_dir)

    vids = [p for p in in_root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    vids.sort()
    print(f"Found {len(vids)} videos.")

    for p in vids:
        label = guess_label(p.name) or "bench"
        out_dir = out_root / label
        print(f"[{label}] -> {p.name}")
        process_video(p, out_dir, label_override=label)

if __name__ == "__main__":
    main()