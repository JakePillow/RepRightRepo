import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from repright.analyser import RepRightAnalyzer


def trunc_video(src: str, frac: float = 0.65) -> str:
    """
    Create a truncated copy of a video by simply cutting bytes is unsafe.
    Instead, we do a "container-respectful" truncation by copying the file
    and letting the pipeline run on fewer frames isn't trivial without ffmpeg trimming.
    For our purposes here we create a shortened file using ffmpeg if available.

    If ffmpeg isn't available in PATH, we fallback to using the same video (no trunc).
    """
    import subprocess

    src_p = Path(src)
    tmp_dir = Path(tempfile.gettempdir())
    out_p = tmp_dir / f"repright_trunc_{src_p.stem}_{next(tempfile._get_candidate_names())}.mp4"

    # Try ffmpeg trim (fast, accurate). If fails, fallback to original.
    try:
        # duration probe
        cmd_probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(src_p)]
        r = subprocess.run(cmd_probe, capture_output=True, text=True)
        if r.returncode != 0:
            return str(src_p)

        dur = float(r.stdout.strip())
        trim = max(0.5, dur * float(frac))

        cmd = [
            "ffmpeg", "-y",
            "-i", str(src_p),
            "-t", f"{trim:.3f}",
            "-c", "copy",
            str(out_p),
        ]
        r2 = subprocess.run(cmd, capture_output=True, text=True)
        if r2.returncode != 0:
            return str(src_p)

        return str(out_p)
    except Exception:
        return str(src_p)


def summarize(label: str, out: dict):
    print(f"\n=== {label} ===")
    print("schema_version:", out.get("schema_version"))
    print("exercise:", out.get("exercise"))
    print("n_reps:", out.get("n_reps"))
    reps = out.get("reps", [])
    if not reps:
        print("NO REPS")
        return

    r0 = reps[0]
    keys = sorted(list(r0.keys()))
    missing = [k for k in ["confidence_v1","biomech_v1","faults_v1","tempo_down_inferred","tempo_down_sec_inferred","end_frame_source"] if k not in r0]
    print("missing_rep_keys:", missing)
    print("start:", r0.get("start_frame"), "peak:", r0.get("peak_frame"), "end:", r0.get("end_frame"))
    print("tempo_up:", r0.get("tempo_up_sec"), "tempo_down:", r0.get("tempo_down_sec"))
    print("tempo_down_inferred:", r0.get("tempo_down_inferred"))
    print("tempo_down_sec_inferred:", r0.get("tempo_down_sec_inferred"))
    print("end_frame_source:", r0.get("end_frame_source"))
    print("confidence:", r0.get("confidence_v1"))
    print("faults:", r0.get("faults_v1"))


def main():
    an = RepRightAnalyzer()

    full = an.analyze(r"C:\\Users\\jakep\\OneDrive\\Desktop\\Dissertation- RepRight\\Dissertation-Rep-Right\\RepRightRepo\\data\\raw\\curl\\barbell biceps curl_1.mp4", "curl")
    summarize("FULL", full)

    trunc = trunc_video(r"C:\\Users\\jakep\\OneDrive\\Desktop\\Dissertation- RepRight\\Dissertation-Rep-Right\\RepRightRepo\\data\\raw\\curl\\barbell biceps curl_1.mp4", frac=0.65)
    trunc_out = an.analyze(trunc, "curl")
    summarize("TRUNC", trunc_out)

    # Compare rep0 if both exist
    fr = full.get("reps", [])
    tr = trunc_out.get("reps", [])
    if fr and tr:
        f0 = fr[0]
        t0 = tr[0]
        print("\n=== DIFF (TRUNC - FULL) ===")
        try:
            print("tempo_down_sec diff:", (t0.get("tempo_down_sec",0.0) - f0.get("tempo_down_sec",0.0)))
        except Exception:
            pass
        print("confidence_full:", f0.get("confidence_v1"))
        print("confidence_trunc:", t0.get("confidence_v1"))
        print("tempo_down_inferred_full:", f0.get("tempo_down_inferred"))
        print("tempo_down_inferred_trunc:", t0.get("tempo_down_inferred"))
        print("end_frame_source_full:", f0.get("end_frame_source"))
        print("end_frame_source_trunc:", t0.get("end_frame_source"))
        print("faults_full:", f0.get("faults_v1"))
        print("faults_trunc:", t0.get("faults_v1"))
        print("\nTrunc video used:", trunc)


if __name__ == "__main__":
    main()
