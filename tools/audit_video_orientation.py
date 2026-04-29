#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import cv2


def ffprobe_json(video: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return {"error": "ffprobe not found in PATH"}

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_streams",
        "-show_entries", "stream=index,codec_name,width,height,avg_frame_rate,side_data_list:stream_tags=rotate",
        "-of", "json",
        str(video),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        return {"error": f"failed to parse ffprobe output: {exc}"}


def opencv_info(video: Path) -> dict:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        return {"error": "OpenCV could not open video"}
    try:
        return {
            "frame_width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
            "frame_height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
            "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
        }
    finally:
        cap.release()


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit video orientation metadata vs OpenCV decode dimensions.")
    ap.add_argument("video", help="Path to video file")
    args = ap.parse_args()

    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        raise SystemExit(f"Video not found: {video}")

    report = {
        "video": str(video),
        "ffprobe": ffprobe_json(video),
        "opencv": opencv_info(video),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
