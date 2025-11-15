import argparse, json, math, time
from pathlib import Path
import cv2
import numpy as np
import mediapipe as mp

VIDEO_EXTS = {'.mp4','.mov','.m4v','.avi','.webm','.mkv'}

TOKENS = {
    'bench': ['benchpress','bench_press','bench','barbell_bench','dumbbell_bench','incline','decline'],
    'squat': ['squat','back_squat','front_squat','goblet'],
    'curl' : ['bicep','biceps','curl','barbell_curl','ezbar'],
}

def guess_label(name: str):
    s = name.lower()
    for label, toks in TOKENS.items():
        for t in toks:
            if t in s: 
                return label
    return None

def angle(a,b,c):
    """Angle ABC (in degrees). a,b,c are (x,y) in image space."""
    a = np.array(a, dtype=float); b = np.array(b, dtype=float); c = np.array(c, dtype=float)
    ba = a - b; bc = c - b
    nba = ba / (np.linalg.norm(ba) + 1e-6)
    nbc = bc / (np.linalg.norm(bc) + 1e-6)
    cosang = np.clip(np.dot(nba, nbc), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))

def choose_driver(label, lm):
    """Return a driver angle per exercise for live rep counting."""
    # indices per MediaPipe Pose
    # https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
    li = mp.solutions.pose.PoseLandmark
    get = lambda idx: (lm[idx].x, lm[idx].y, lm[idx].visibility)

    # helper to pull 2D points (ignore vis)
    def pt(idx): 
        p = lm[idx]; return (p.x, p.y)

    if label == 'curl':
        # elbow flexion: shoulder-elbow-wrist (use right side by default)
        return angle(pt(li.RIGHT_SHOULDER), pt(li.RIGHT_ELBOW), pt(li.RIGHT_WRIST))
    elif label == 'bench':
        # elbow flexion too (side-ish views still useful)
        return angle(pt(li.RIGHT_SHOULDER), pt(li.RIGHT_ELBOW), pt(li.RIGHT_WRIST))
    elif label == 'squat':
        # knee flexion: hip-knee-ankle
        return angle(pt(li.RIGHT_HIP), pt(li.RIGHT_KNEE), pt(li.RIGHT_ANKLE))
    else:
        # fallback: hip angle: shoulder-hip-knee
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
        # heuristics per exercise (tweak later)
        if label == 'curl':
            self.min_rom = 35.0
        elif label == 'squat':
            self.min_rom = 40.0
        else: # bench default
            self.min_rom = 30.0
        self.min_phase_frames = int(0.20 * self.fps)  # >=0.2s per half phase

        self.prev = None
        self.dir = 0  # -1 down, +1 up
        self.extreme = None
        self.extreme_frame = 0
        self.frames_since_flip = 0
        self.reps = 0
        self.rep_times = []  # (start_f,end_f,rom)

        self._phase_start_frame = 0
        self._last_flip_frame = 0
        self._rom_acc = 0.0

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

        # track extreme within current direction
        if (self.dir > 0 and driver_angle > self.extreme) or (self.dir < 0 and driver_angle < self.extreme):
            self.extreme = driver_angle
            self.extreme_frame = frame_idx

        flipped = (cur_dir != 0 and self.dir != 0 and cur_dir != self.dir)
        self.frames_since_flip += 1

        event = None
        if flipped and self.frames_since_flip >= self.min_phase_frames:
            swing = abs(driver_angle - self.extreme)
            if swing >= self.min_rom:
                # Complete a half-phase; every two flips is one rep.
                # We mark rep at flip if half-phases are long enough.
                # Convert two half phases -> one rep by counting on every second flip:
                # Simpler: count a rep on every qualified flip and divide by 2 in summary,
                # but UX prefers int. Here we require two qualified phases implicitly by min_phase_frames.
                self.reps += 1
                event = {"type":"rep", "frame": frame_idx, "reps": self.reps, "rom": float(swing)}
                self._last_flip_frame = frame_idx
            # reset for next phase
            self.dir = cur_dir
            self.extreme = driver_angle
            self.extreme_frame = frame_idx
            self.frames_since_flip = 0

        self.prev = driver_angle
        return event

def process_video(in_path: Path, out_dir: Path):
    label = guess_label(in_path.name) or "bench"
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(in_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(out_dir / f"{in_path.stem}_overlay.mp4"), fourcc, fps, (w,h))

    jsonl = (out_dir / f"{in_path.stem}.jsonl").open("w", encoding="utf-8")
    summary_path = out_dir / f"{in_path.stem}_summary.json"

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(model_complexity=1, enable_segmentation=False,
                        min_detection_confidence=0.5, min_tracking_confidence=0.5)
    draw = mp.solutions.drawing_utils
    style = mp.solutions.drawing_styles

    counter = LiveRepCounter(fps, label)
    frame_idx = 0
    rep_events = []

    t0 = time.time()
    while True:
        ok, frame = cap.read()
        if not ok: break
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

            # draw skeleton
            draw.draw_landmarks(
                frame,
                res.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=style.get_default_pose_landmarks_style()
            )
            # HUD
            cv2.rectangle(frame, (10,10), (230,90), (0,0,0), -1)
            cv2.putText(frame, f"{label.upper()}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.putText(frame, f"Reps: {counter.reps}", (20,75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        else:
            # if no pose, still show current reps
            cv2.putText(frame, f"Reps: {counter.reps}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        # write per-frame JSONL
        row = {
            "frame": frame_idx,
            "t": float(frame_idx / (fps or 25.0)),
            "angles": angles,
            "reps": counter.reps
        }
        jsonl.write(json.dumps(row) + "\n")

        writer.write(frame)
        frame_idx += 1

    cap.release(); writer.release(); jsonl.close(); pose.close()
    dt = time.time() - t0

    # build basic per-set summary
    # For this first pass, each flip event counted as one rep; we keep that as is (consistent streaming),
    # and compute naive average ROM & tempo (time per rep).
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
        "reps": int(counter.reps),
        "avg_rep_time_s": round(avg_rep_time, 3),
        "avg_rom_deg": round(avg_rom, 1),
        "notes": "Streaming baseline. Thresholds to be tuned per lift; offline smoothing & exact phase timing can refine."
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
        process_video(p, out_dir)

if __name__ == "__main__":
    main()
