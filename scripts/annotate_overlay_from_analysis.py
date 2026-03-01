from __future__ import annotations

import argparse
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


def _transcode_with_ffmpeg(src: Path, dst: Path, args: list[str]) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    cmd = [ffmpeg, "-y", "-i", str(src), *args, str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    return _valid_video_file(dst)


def _build_rep_ranges(analysis: dict) -> list[tuple[int, int, int]]:
    reps = analysis.get("reps") if isinstance(analysis.get("reps"), list) else []
    out: list[tuple[int, int, int]] = []
    for rep in reps:
        if not isinstance(rep, dict):
            continue
        idx = rep.get("rep_index")
        sf = rep.get("start_frame")
        ef = rep.get("end_frame")
        if isinstance(idx, int) and isinstance(sf, int) and isinstance(ef, int) and ef >= sf:
            out.append((sf, ef, idx))
    out.sort(key=lambda x: x[0])
    return out


def _rep_count_completed(frame_idx: int, rep_ranges: list[tuple[int, int, int]]) -> int:
    count = 0
    for sf, ef, _idx in rep_ranges:
        if frame_idx >= ef:
            count += 1
        else:
            break
    return count


def _active_rep(frame_idx: int, rep_ranges: list[tuple[int, int, int]]) -> int | None:
    for sf, ef, idx in rep_ranges:
        if sf <= frame_idx <= ef:
            return idx
    return None


def annotate_overlay(overlay: Path, analysis_json: Path, out_path: Path) -> Path:
    analysis = json.loads(analysis_json.read_text(encoding="utf-8"))
    exercise = str(analysis.get("exercise") or "lift").upper()
    rep_ranges = _build_rep_ranges(analysis)

    cap = cv2.VideoCapture(str(overlay))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    raw_out = out_path.with_suffix(".raw.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(raw_out), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open writer for {raw_out}")

    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            reps_completed = _rep_count_completed(frame_idx, rep_ranges)
            active = _active_rep(frame_idx, rep_ranges)

            cv2.rectangle(frame, (10, 10), (330, 120), (0, 0, 0), -1)
            cv2.putText(frame, exercise, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"Reps: {reps_completed}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            if active is not None:
                cv2.putText(frame, f"Rep {active}", (20, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 210, 80), 2)

            writer.write(frame)
            frame_idx += 1
    finally:
        cap.release()
        writer.release()

    # reliable output selection
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final = out_path
    h264_ok = _transcode_with_ffmpeg(raw_out, out_path, ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    if not h264_ok:
        webm_path = out_path.with_suffix(".webm")
        vp9_ok = _transcode_with_ffmpeg(raw_out, webm_path, ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32"])
        if vp9_ok:
            final = webm_path
        elif _valid_video_file(raw_out):
            raw_out.replace(out_path)
            final = out_path
        else:
            raise RuntimeError("Annotated overlay output invalid after transcode attempts")

    if raw_out.exists() and raw_out != final:
        raw_out.unlink(missing_ok=True)

    if not _valid_video_file(final):
        raise RuntimeError(f"Annotated overlay invalid: {final}")
    return final


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    final = annotate_overlay(Path(args.overlay), Path(args.analysis), Path(args.out))
    print(str(final))


if __name__ == "__main__":
    main()
