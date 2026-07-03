from __future__ import annotations

import subprocess
from pathlib import Path

from repright.video_orientation import (
    VideoStreamProbe,
    _stream_probe_from_payload,
    enable_capture_autorotation,
    normalize_video_orientation,
)


def test_display_matrix_is_authoritative_and_normalizes_signed_180() -> None:
    probe = _stream_probe_from_payload(
        {
            "streams": [
                {
                    "codec_name": "h264",
                    "pix_fmt": "yuv420p",
                    "width": 1920,
                    "height": 1080,
                    "tags": {"rotate": "90"},
                    "side_data_list": [{"rotation": -180.0}],
                }
            ]
        }
    )

    assert probe.rotation == 180
    assert (probe.width, probe.height) == (1920, 1080)


def test_zero_rotation_uses_original_video_without_reencoding(tmp_path, monkeypatch) -> None:
    src = tmp_path / "desktop.mp4"
    src.write_bytes(b"video")
    monkeypatch.setattr(
        "repright.video_orientation.probe_video_stream",
        lambda _src: VideoStreamProbe(width=1280, height=720, rotation=0),
    )

    result = normalize_video_orientation(src, tmp_path / "run")

    assert result.path == src
    assert result.normalized is False
    assert result.source_rotation == 0


def test_opencv_fallback_explicitly_enables_mobile_autorotation() -> None:
    import cv2

    class FakeCapture:
        def __init__(self) -> None:
            self.autorotate = 0.0

        def get(self, property_id):
            if property_id == cv2.CAP_PROP_ORIENTATION_META:
                return 180.0
            if property_id == cv2.CAP_PROP_ORIENTATION_AUTO:
                return self.autorotate
            return 0.0

        def set(self, property_id, value):
            if property_id == cv2.CAP_PROP_ORIENTATION_AUTO:
                self.autorotate = float(value)
                return True
            return False

    capture = FakeCapture()

    assert enable_capture_autorotation(capture, Path("phone.mov")) == 180
    assert capture.autorotate == 1.0


def test_mobile_180_rotation_uses_ffmpeg_autorotate_and_clears_metadata(
    tmp_path, monkeypatch
) -> None:
    src = tmp_path / "phone.mov"
    src.write_bytes(b"mobile-video")
    probes = iter(
        [
            VideoStreamProbe(width=1920, height=1080, rotation=180),
            VideoStreamProbe(width=1920, height=1080, rotation=0),
        ]
    )
    monkeypatch.setattr(
        "repright.video_orientation.probe_video_stream",
        lambda _src: next(probes),
    )
    monkeypatch.setattr(
        "repright.video_orientation.shutil.which",
        lambda executable: "ffmpeg" if executable == "ffmpeg" else None,
    )
    commands: list[list[str]] = []

    def fake_run(cmd, capture_output, text):
        commands.append(cmd)
        Path(cmd[-1]).write_bytes(b"upright-video")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("repright.video_orientation.subprocess.run", fake_run)

    result = normalize_video_orientation(src, tmp_path / "run")

    assert result.normalized is True
    assert result.source_rotation == 180
    assert result.path.name == "phone_upright_v1.mp4"
    cmd = commands[0]
    assert "-autorotate" in cmd
    assert "-noautorotate" not in cmd
    assert cmd[cmd.index("-map_metadata") + 1] == "-1"
    assert cmd[cmd.index("-metadata:s:v:0") + 1] == "rotate=0"
    assert not any("hflip" in arg or "transpose" in arg for arg in cmd)


def test_browser_transcode_also_delegates_signed_rotation_to_ffmpeg(
    tmp_path, monkeypatch
) -> None:
    from ui.components import panels

    src = tmp_path / "legacy-overlay.mp4"
    dst = tmp_path / "legacy-overlay_browser_orientation_v2.mp4"
    src.write_bytes(b"legacy")
    monkeypatch.setattr(panels.shutil, "which", lambda _executable: "ffmpeg")
    commands: list[list[str]] = []

    def fake_run(cmd, capture_output, text):
        commands.append(cmd)
        Path(cmd[-1]).write_bytes(b"x" * (51 * 1024))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(panels.subprocess, "run", fake_run)

    assert panels._transcode_to_browser_mp4(src, dst) == dst
    cmd = commands[0]
    assert "-autorotate" in cmd
    assert "-noautorotate" not in cmd
    assert not any("hflip" in arg or "transpose" in arg for arg in cmd)
