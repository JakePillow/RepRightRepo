import subprocess
import tempfile
from pathlib import Path

from repright.analyzer import RepRightAnalyzer


def run_ffmpeg_trim(src: str, out_path: str, trim_sec: float) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", src,
        "-t", f"{trim_sec:.3f}",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg trim failed:\n" + r.stderr[-1500:])


def summarize(label: str, out: dict):
    print(f"\n=== {label} ===")
    print("schema_version:", out.get("schema_version"))
    print("exercise:", out.get("exercise"))
    print("n_reps:", out.get("n_reps"))
    reps = out.get("reps", [])
    if not reps:
        print("NO REPS")
        return None
    r0 = reps[0]
    print("start:", r0.get("start_frame"), "peak:", r0.get("peak_frame"), "end:", r0.get("end_frame"))
    print("tempo_up:", r0.get("tempo_up_sec"), "tempo_down:", r0.get("tempo_down_sec"))
    print("tempo_down_inferred:", r0.get("tempo_down_inferred"))
    print("end_frame_source:", r0.get("end_frame_source"))
    print("confidence:", r0.get("confidence_v1"))
    print("faults:", r0.get("faults_v1"))
    return r0


def main():
    an = RepRightAnalyzer()

    full = an.analyze(r"C:\\Users\\jakep\\OneDrive\\Desktop\\Dissertation- RepRight\\Dissertation-Rep-Right\\RepRightRepo\\data\\raw\\bench\\bench press_48.mp4", "bench")
    r0_full = summarize("FULL", full)
    if r0_full is None:
        raise SystemExit("FULL had 0 reps — can't build trunc test from this clip.")

    raw = full.get("raw", {}) or {}
    fps = float(raw.get("fps", 0.0) or 0.0)
    if fps <= 0:
        raise SystemExit(f"Invalid fps in output raw.fps: {raw.get('fps')}")

    peak = int(r0_full["peak_frame"])
    buffer_frames = int(round(0.20 * fps))  # 200ms after peak
    trim_frames = peak + buffer_frames
    trim_sec = trim_frames / fps

    src_p = Path(r"C:\\Users\\jakep\\OneDrive\\Desktop\\Dissertation- RepRight\\Dissertation-Rep-Right\\RepRightRepo\\data\\raw\\bench\\bench press_48.mp4")
    out_p = Path(tempfile.gettempdir()) / f"repright_trunc_after_peak_{src_p.stem}_{next(tempfile._get_candidate_names())}.mp4"

    print("\nTrunc plan:")
    print("fps:", fps)
    print("peak_frame:", peak)
    print("buffer_frames:", buffer_frames)
    print("trim_frames:", trim_frames)
    print("trim_sec:", trim_sec)
    print("trunc_out:", str(out_p))

    run_ffmpeg_trim(str(src_p), str(out_p), trim_sec)

    trunc_out = an.analyze(str(out_p), "bench")
    r0_trunc = summarize("TRUNC", trunc_out)

    if r0_trunc and r0_full:
        print("\n=== DIFF (TRUNC - FULL) ===")
        td_full = float(r0_full.get("tempo_down_sec", 0.0) or 0.0)
        td_tr = float(r0_trunc.get("tempo_down_sec", 0.0) or 0.0)
        print("tempo_down_sec diff:", td_tr - td_full)
        print("confidence_full:", r0_full.get("confidence_v1"))
        print("confidence_trunc:", r0_trunc.get("confidence_v1"))
        print("tempo_down_inferred_full:", r0_full.get("tempo_down_inferred"))
        print("tempo_down_inferred_trunc:", r0_trunc.get("tempo_down_inferred"))
        print("end_frame_source_full:", r0_full.get("end_frame_source"))
        print("end_frame_source_trunc:", r0_trunc.get("end_frame_source"))

if __name__ == "__main__":
    main()
