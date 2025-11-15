import argparse, shutil, re
from pathlib import Path
import cv2

VIDEO_EXTS = {".mp4",".mov",".m4v",".avi",".webm",".mkv"}
TOKENS = {
    "bench": ["benchpress","bench_press","bench","barbell_bench","dumbbell_bench","incline","decline"],
    "squat": ["squat","back_squat","front_squat","goblet"],
    "curl" : ["bicep","biceps","curl","barbell_curl","dumbbell_curl","ezbar"],
}

def guess_label(name: str):
    s = name.lower()
    for label, toks in TOKENS.items():
        for t in toks:
            if re.search(rf"(?<![a-z]){re.escape(t)}(?![a-z])", s):
                return label
    return None

def meta_ok(p: Path, minw: int, minh: int, minfps: float):
    cap = cv2.VideoCapture(str(p))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    cap.release()
    if w==0 or h==0 or fps==0: 
        return False, (w,h,fps)
    return (w>=minw and h>=minh and fps>=minfps), (w,h,fps)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="root with raw datasets")
    ap.add_argument("--dst", required=True, help="shortlist root")
    ap.add_argument("--minw", type=int, default=960)
    ap.add_argument("--minh", type=int, default=540)
    ap.add_argument("--minfps", type=float, default=25.0)
    args = ap.parse_args()

    src = Path(args.src); dst = Path(args.dst)
    counts = {"bench":0,"squat":0,"curl":0,"other":0}

    for p in src.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in VIDEO_EXTS: 
            continue
        label = guess_label(p.name) or "other"
        ok,_ = meta_ok(p, args.minw, args.minh, args.minfps)
        if label in ("bench","squat","curl"):
            bucket = "clean" if ok else "noisy"
            out = dst/label/bucket
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out/p.name)
            counts[label]+=1
        else:
            counts["other"]+=1

    print("Copied counts:", counts)

if __name__ == "__main__":
    main()
