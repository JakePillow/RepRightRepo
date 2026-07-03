from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoStreamProbe:
    codec: str | None = None
    pix_fmt: str | None = None
    width: int | None = None
    height: int | None = None
    rotation: int | None = None


@dataclass(frozen=True)
class OrientationNormalization:
    path: Path
    source_rotation: int | None
    source_width: int | None
    source_height: int | None
    output_width: int | None
    output_height: int | None
    normalized: bool


def enable_capture_autorotation(capture: Any, src: Path | None = None) -> int | None:
    """Tell OpenCV's FFmpeg/AVFoundation backend to honor stream rotation."""
    try:
        import cv2

        raw_rotation = capture.get(cv2.CAP_PROP_ORIENTATION_META)
        rotation = _rotation_degrees(raw_rotation)
        capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
        autorotate_enabled = bool(capture.get(cv2.CAP_PROP_ORIENTATION_AUTO))
    except Exception as exc:
        logging.warning(
            "[VIDEO ORIENTATION] OpenCV orientation controls unavailable for %s: %s",
            src,
            exc,
        )
        return None

    if rotation not in (None, 0) and not autorotate_enabled:
        logging.warning(
            "[VIDEO ORIENTATION] OpenCV backend reported rotation=%s but rejected autorotation for %s",
            rotation,
            src,
        )
    else:
        logging.info(
            "[VIDEO ORIENTATION] OpenCV source=%s rotation=%s autorotate=%s",
            src,
            rotation,
            autorotate_enabled,
        )
    return rotation


def _rotation_degrees(value: Any) -> int | None:
    if value is None:
        return None
    try:
        rotation = int(round(float(value))) % 360
    except (TypeError, ValueError):
        return None

    # Display matrices occasionally produce values a fraction of a degree away
    # from a quarter turn. Snap those values so the orientation contract remains
    # deterministic.
    for quarter_turn in (0, 90, 180, 270):
        distance = abs(rotation - quarter_turn)
        distance = min(distance, 360 - distance)
        if distance <= 1:
            return quarter_turn
    return rotation


def _stream_probe_from_payload(payload: dict[str, Any]) -> VideoStreamProbe:
    streams = payload.get("streams") or []
    stream = streams[0] if streams and isinstance(streams[0], dict) else {}

    rotation: int | None = None
    # The display matrix is authoritative when both it and the legacy rotate
    # tag exist. ffprobe commonly reports its value with a negative sign; only
    # ffmpeg's autorotation should interpret that sign.
    for entry in stream.get("side_data_list") or []:
        if not isinstance(entry, dict):
            continue
        candidate = _rotation_degrees(entry.get("rotation"))
        if candidate is not None:
            rotation = candidate
            break

    if rotation is None:
        tags = stream.get("tags") or {}
        if isinstance(tags, dict):
            rotation = _rotation_degrees(tags.get("rotate"))

    def _optional_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    return VideoStreamProbe(
        codec=stream.get("codec_name"),
        pix_fmt=stream.get("pix_fmt"),
        width=_optional_int(stream.get("width")),
        height=_optional_int(stream.get("height")),
        rotation=rotation if rotation is not None else 0,
    )


def probe_video_stream(src: Path) -> VideoStreamProbe:
    """Read codec and display-orientation metadata from the first video stream."""
    src = Path(src)
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        logging.warning("[VIDEO ORIENTATION] ffprobe is unavailable for %s", src)
        return VideoStreamProbe()

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,pix_fmt,width,height:stream_tags=rotate:stream_side_data=rotation",
        "-of", "json",
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logging.warning(
            "[VIDEO ORIENTATION] ffprobe failed for %s: %s",
            src,
            proc.stderr.strip()[:240],
        )
        return VideoStreamProbe()

    try:
        payload = json.loads(proc.stdout or "{}")
    except (TypeError, json.JSONDecodeError):
        logging.warning("[VIDEO ORIENTATION] invalid ffprobe JSON for %s", src)
        return VideoStreamProbe()
    return _stream_probe_from_payload(payload)


def normalize_video_orientation(src: Path, output_dir: Path) -> OrientationNormalization:
    """
    Return an input whose pixels are physically upright and rotation metadata is zero.

    Files with no display rotation take the zero-copy path. Rotated mobile files are
    decoded with ffmpeg's autorotation enabled, so ffmpeg—not application code—handles
    signed display-matrix semantics.
    """
    src = Path(src)
    output_dir = Path(output_dir)
    source_probe = probe_video_stream(src)

    if source_probe.rotation == 0:
        logging.info(
            "[VIDEO ORIENTATION] source=%s rotation=0 dimensions=%sx%s action=passthrough",
            src,
            source_probe.width,
            source_probe.height,
        )
        return OrientationNormalization(
            path=src,
            source_rotation=0,
            source_width=source_probe.width,
            source_height=source_probe.height,
            output_width=source_probe.width,
            output_height=source_probe.height,
            normalized=False,
        )

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        if source_probe.rotation is None:
            # Keep non-ffmpeg development environments working, but make the
            # missing guarantee visible. Production installs both tools via
            # packages.txt.
            logging.warning(
                "[VIDEO ORIENTATION] orientation is unknown for %s; processing original bytes",
                src,
            )
            return OrientationNormalization(
                path=src,
                source_rotation=None,
                source_width=source_probe.width,
                source_height=source_probe.height,
                output_width=source_probe.width,
                output_height=source_probe.height,
                normalized=False,
            )
        raise RuntimeError(
            f"Video has {source_probe.rotation}° display rotation, but ffmpeg is unavailable; "
            "cannot create an upright analysis input."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    dst = output_dir / f"{src.stem}_upright_v1.mp4"
    cmd = [
        ffmpeg,
        "-y",
        "-autorotate",
        "-i", str(src),
        "-map", "0:v:0",
        "-an",
        "-map_metadata", "-1",
        "-metadata:s:v:0", "rotate=0",
        "-vf", "setsar=1,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-movflags", "+faststart",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        dst.unlink(missing_ok=True)
        detail = proc.stderr.strip()[-500:] if proc.stderr else "no output produced"
        raise RuntimeError(f"Could not normalize mobile video orientation: {detail}")

    output_probe = probe_video_stream(dst)
    if output_probe.rotation not in (0, None):
        dst.unlink(missing_ok=True)
        raise RuntimeError(
            f"Orientation normalization left a {output_probe.rotation}° display rotation on {dst.name}."
        )

    logging.info(
        "[VIDEO ORIENTATION] source=%s rotation=%s dimensions=%sx%s "
        "output=%s rotation=%s dimensions=%sx%s action=normalized",
        src,
        source_probe.rotation,
        source_probe.width,
        source_probe.height,
        dst,
        output_probe.rotation,
        output_probe.width,
        output_probe.height,
    )
    return OrientationNormalization(
        path=dst,
        source_rotation=source_probe.rotation,
        source_width=source_probe.width,
        source_height=source_probe.height,
        output_width=output_probe.width,
        output_height=output_probe.height,
        normalized=True,
    )
