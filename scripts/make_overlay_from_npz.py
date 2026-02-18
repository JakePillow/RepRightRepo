from __future__ import annotations
import argparse
from pathlib import Path

import cv2
import numpy as np


# MediaPipe Pose landmark indices (33)
# We'll draw a basic but clear skeleton:
EDGES = [
    (11,12), (11,13), (13,15), (12,14), (14,16),         # arms
    (11,23), (12,24), (23,24),                             # torso
    (23,25), (25,27), (24,26), (26,28),                    # legs
    (27,31), (28,32),                                      # feet
    (0,1), (1,2), (2,3), (3,7), (0,4), (4,5), (5,6), (6,8) # face-ish
]


def to_pixels(xy: np.ndarray, w: int, h: int) -> np.ndarray:
    """
    xy: (N,2). If it looks normalized (max <= ~2), clamp to [0,1] and scale to pixels.
    If it looks like pixel coords already (max > ~10), keep as-is.
    """
    xy = xy.astype(np.float32)
    mx = np.nanmax(xy)
    if mx <= 2.5:  # normalized-ish (your y goes to ~1.7)
        xy[:, 0] = np.clip(xy[:, 0], 0.0, 1.0) * float(w)
        xy[:, 1] = np.clip(xy[:, 1], 0.0, 1.0) * float(h)
    return xy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--npz", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    video_path = Path(args.video)
    npz_path   = Path(args.npz)
    out_path   = Path(args.out)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

    d = np.load(str(npz_path))
    pose = d["pose"]  # (T,33,4) expected; use [:,:,:2]
    T = int(pose.shape[0])

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    tmp_out = out_path.with_name(out_path.stem + ".tmp_mp4v.mp4")
    tmp_out.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(tmp_out), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError("VideoWriter failed to open (mp4v).")

    t = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if t < T:
            xy = pose[t, :, :2]
            xy = to_pixels(xy, w, h)

            # draw edges
            for a, b in EDGES:
                xa, ya = xy[a]
                xb, yb = xy[b]
                if np.isfinite(xa) and np.isfinite(ya) and np.isfinite(xb) and np.isfinite(yb):
                    cv2.line(frame, (int(xa), int(ya)), (int(xb), int(yb)), (0,255,0), 2)

            # draw joints
            for j in range(min(33, xy.shape[0])):
                xj, yj = xy[j]
                if np.isfinite(xj) and np.isfinite(yj):
                    cv2.circle(frame, (int(xj), int(yj)), 4, (0,0,255), -1)

        writer.write(frame)
        t += 1

    cap.release()
    writer.release()

    # Transcode to H.264 for browser/Streamlit reliability
    # (use ffmpeg if available; if not, keep tmp mp4v)
    import shutil, subprocess
    ff = shutil.which("ffmpeg")
    if ff:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            ff, "-y",
            "-i", str(tmp_out),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        try:
            tmp_out.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        tmp_out.replace(out_path)

    print(str(out_path).replace("\\","/"))


if __name__ == "__main__":
    main()
