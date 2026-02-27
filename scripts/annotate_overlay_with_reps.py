from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2

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


def _transcode_h264_faststart(src: Path, dst: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg, "-y",
        "-i", str(src),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[warn] ffmpeg transcode failed: {proc.stderr.strip()[:250]}")
        return False
    return _valid_video_file(dst)


def _current_rep_index(frame_idx: int, reps: list[dict]) -> int | None:
    """
    Return 1-based rep index if frame is within a rep interval, else None.
    """
    for r in reps:
        if not isinstance(r, dict):
            continue
        sf = r.get("start_frame")
        ef = r.get("end_frame")
        ri = r.get("rep_index")
        if isinstance(sf, int) and isinstance(ef, int) and isinstance(ri, int):
            if sf <= frame_idx <= ef:
                return ri
    return None


def annotate_overlay_with_offline_reps(
    overlay_in: Path,
    analysis_json: Path,
    overlay_out: Path,
) -> Path:
    overlay_in = Path(overlay_in)
    analysis_json = Path(analysis_json)
    overlay_out = Path(overlay_out)

    if not overlay_in.exists():
        raise FileNotFoundError(f"Overlay input missing: {overlay_in}")
    if not analysis_json.exists():
        raise FileNotFoundError(f"Analysis json missing: {analysis_json}")

    analysis = json.loads(analysis_json.read_text(encoding="utf-8"))
    reps = analysis.get("reps") or []
    if not isinstance(reps, list):
        reps = []

    total_reps = (analysis.get("set_summary_v1") or {}).get("n_reps")
    if not isinstance(total_reps, int):
        total_reps = len(reps)

    cap = cv2.VideoCapture(str(overlay_in))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open overlay video: {overlay_in}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or 640
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or 480

    tmp_mp4v = overlay_out.with_suffix(".tmp_mp4v.mp4")
    tmp_mp4v.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(tmp_mp4v), fourcc, fps, (w, h))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"VideoWriter failed to open: {tmp_mp4v}")

    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            cur_rep = _current_rep_index(frame_idx, reps)

            # HUD box
            cv2.rectangle(frame, (10, 10), (320, 105), (0, 0, 0), -1)
            cv2.putText(
                frame,
                f"REPS (offline): {total_reps}",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (0, 255, 0),
                2,
            )

            if cur_rep is not None:
                cv2.putText(
                    frame,
                    f"Rep: {cur_rep}/{max(total_reps, 1)}",
                    (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.85,
                    (255, 255, 255),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    "Rep: -",
                    (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.85,
                    (180, 180, 180),
                    2,
                )

            writer.write(frame)
            frame_idx += 1

    finally:
        cap.release()
        writer.release()

    # Prefer H.264 output for Streamlit/Chrome reliability
    overlay_out.parent.mkdir(parents=True, exist_ok=True)
    if _transcode_h264_faststart(tmp_mp4v, overlay_out):
        try:
            tmp_mp4v.unlink(missing_ok=True)
        except Exception:
            pass
        return overlay_out

    # Fallback: keep mp4v if ffmpeg missing/fails
    tmp_mp4v.replace(overlay_out)
    return overlay_out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay-in", required=True)
    ap.add_argument("--analysis-json", required=True)
    ap.add_argument("--overlay-out", required=True)
    args = ap.parse_args()

    out = annotate_overlay_with_offline_reps(
        overlay_in=Path(args.overlay_in),
        analysis_json=Path(args.analysis_json),
        overlay_out=Path(args.overlay_out),
    )
    print(str(out).replace("\\", "/"))


if __name__ == "__main__":
    main()