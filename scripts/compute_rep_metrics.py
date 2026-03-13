from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from repright.summary_v1 import build_set_summary_v1


def read_driver_angle(jsonl_path: Path) -> tuple[list[int], list[float]]:
    frames: list[int] = []
    angles: list[float] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ang = (row.get("angles") or {}).get("driver")
            if ang is None:
                continue
            try:
                frames.append(int(row.get("frame", 0)))
                angles.append(float(ang))
            except (TypeError, ValueError):
                continue
    return frames, angles


def smooth(x: list[float], win: int = 5) -> list[float]:
    if not x:
        return []
    out: list[float] = []
    h = win // 2
    for i in range(len(x)):
        lo = max(0, i - h)
        hi = min(len(x), i + h + 1)
        out.append(sum(x[lo:hi]) / (hi - lo))
    return out


def detect_reps(
    frames: list[int],
    a: list[float],
    fps: float,
    min_rom_deg: float = 10.0,
    min_gap_sec: float = 0.2,
    hyst_frac: float = 0.08,
    min_rep_duration_sec: float = 0.30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(a) < 10:
        return [], {"reason": "too_short", "len": len(a)}

    amin, amax = min(a), max(a)
    rom_total = amax - amin
    if rom_total <= 0:
        return [], {"reason": "flat_signal", "len": len(a)}

    low = amin + 0.25 * rom_total
    high = amax - 0.25 * rom_total
    h = hyst_frac * rom_total
    high_enter = high
    high_exit = high + h
    low_enter = low

    reps: list[dict[str, Any]] = []
    state = "top"
    start_i: int | None = None
    peak_i: int | None = None
    last_start_frame: int | None = None

    for i in range(1, len(a)):
        prev, cur = a[i - 1], a[i]

        if state == "top":
            if prev > high_enter and cur <= high_enter:
                f0cand = frames[i]
                if last_start_frame is not None and (f0cand - last_start_frame) / fps < min_gap_sec:
                    continue
                state = "down"
                start_i = i
                peak_i = None
                last_start_frame = frames[i]

        elif state == "down":
            if peak_i is None or cur < a[peak_i]:
                peak_i = i
            if prev < low_enter and cur >= low_enter:
                state = "up"

        elif state == "up":
            if prev < high_exit and cur >= high_exit and start_i is not None and peak_i is not None:
                end_i = i
                f0, fp, f1 = frames[start_i], frames[peak_i], frames[end_i]
                dur = (f1 - f0) / fps
                seg = a[start_i : end_i + 1]
                rom_deg = float(max(seg) - min(seg))
                if dur >= min_rep_duration_sec and rom_deg >= min_rom_deg:
                    tempo_down = max(0.0, (fp - f0) / fps)
                    tempo_up = max(0.0, (f1 - fp) / fps)
                    reps.append(
                        {
                            "start_frame": int(f0),
                            "peak_frame": int(fp),
                            "end_frame": int(f1),
                            "duration_sec": float(dur),
                            "tempo_down_sec": float(tempo_down),
                            "tempo_up_sec": float(tempo_up),
                            "rom_deg": float(rom_deg),
                        }
                    )
                state = "top"
                start_i = None
                peak_i = None

    debug = {
        "signal_min": float(amin),
        "signal_max": float(amax),
        "rom_total": float(rom_total),
        "threshold_low": float(low),
        "threshold_high": float(high),
        "min_rom_deg": float(min_rom_deg),
        "min_rep_duration_sec": float(min_rep_duration_sec),
        "fps": float(fps),
    }
    return reps, debug


def _make_fault(code: str, severity: str, value: float, threshold: float, evidence: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "value": float(value),
        "threshold": float(threshold),
        "evidence": evidence,
    }


def _rep_confidence(rep: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    level = "high"
    if rep["rom"] < 0.18:
        level = "low"
        reasons.append("shallow_rom")
    if rep["duration_sec"] < 0.5:
        level = "medium" if level == "high" else level
        reasons.append("very_fast_rep")
    if not reasons:
        reasons = ["stable_driver_signal"]
    return {"level": level, "reasons": reasons}


def _rep_faults(exercise: str, rep: dict[str, Any]) -> list[dict[str, Any]]:
    faults: list[dict[str, Any]] = []
    if rep["rom"] < 0.2:
        faults.append(
            _make_fault(
                code="LOW_ROM",
                severity="medium" if rep["rom"] >= 0.14 else "high",
                value=rep["rom"],
                threshold=0.2,
                evidence="Normalized ROM below threshold.",
            )
        )

    if rep["tempo_up_sec"] < 0.25:
        faults.append(
            _make_fault(
                code="RUSHED_CONCENTRIC",
                severity="medium",
                value=rep["tempo_up_sec"],
                threshold=0.25,
                evidence="Concentric phase completed faster than threshold.",
            )
        )

    if exercise in {"deadlift", "squat"} and rep["tempo_down_sec"] < 0.20:
        faults.append(
            _make_fault(
                code="LUMBAR_FLEXION",
                severity="medium",
                value=rep["tempo_down_sec"],
                threshold=0.20,
                evidence="Trunk-angle proxy transition was abrupt during lowering phase.",
            )
        )
    return faults


def build_analysis_v1(exercise: str, fps: float, reps_raw: list[dict[str, Any]], rep_debug: dict[str, Any]) -> dict[str, Any]:
    reps: list[dict[str, Any]] = []
    for idx, r in enumerate(reps_raw, start=1):
        driver = "elbow" if exercise in {"bench", "curl"} else "trunk_proxy"
        elbow_rom_deg = float(r["rom_deg"]) if exercise in {"bench", "curl"} else None
        rep = {
            "rep_index": idx,
            "start_frame": int(r["start_frame"]),
            "peak_frame": int(r["peak_frame"]),
            "end_frame": int(r["end_frame"]),
            "rom": float(r["rom_deg"] / 180.0),
            "duration_sec": float(r["duration_sec"]),
            "tempo_up_sec": float(r["tempo_up_sec"]),
            "tempo_down_sec": float(r["tempo_down_sec"]),
            "tempo_down_inferred": False,
            "tempo_down_sec_inferred": float(r["tempo_down_sec"]),
            "end_frame_source": "signal_hysteresis",
            "biomech_v1": {
                "driver_signal": driver,
                "driver_rom_deg": float(r["rom_deg"]),
                "elbow_rom_deg": elbow_rom_deg,
            },
        }
        rep["confidence_v1"] = _rep_confidence(rep)
        rep["faults_v1"] = _rep_faults(exercise, rep)
        reps.append(rep)

    set_summary = build_set_summary_v1(reps)
    set_summary.setdefault("n_reps", len(reps))
    set_summary.setdefault("avg_rom", float(mean([r["rom"] for r in reps])) if reps else 0.0)
    set_summary.setdefault("avg_duration_sec", float(mean([r["duration_sec"] for r in reps])) if reps else 0.0)
    return {
        "schema_version": "analysis_v1",
        "exercise": exercise,
        "fps": fps,
        "reps": reps,
        "set_summary_v1": set_summary,
        "rep_debug": rep_debug,
    }


def compute_rep_metrics_file(exercise: str, jsonl_path: Path, out_path: Path, fps: float = 25.0) -> dict[str, Any]:
    frames, angles = read_driver_angle(jsonl_path)

    a_s = smooth(angles, win=5)

    detect_kwargs: dict[str, float] = {}
    if exercise == "curl":
        detect_kwargs = {
            "min_rom_deg": 7.0,
            "min_rep_duration_sec": 0.25,
        }

    # Run detection on normal signal
    reps_raw_1, debug_1 = detect_reps(frames, a_s, fps, **detect_kwargs)

    # Run detection on inverted signal (polarity robustness)
    a_inv = [-v for v in a_s]
    reps_raw_2, debug_2 = detect_reps(frames, a_inv, fps, **detect_kwargs)

    # Deterministic selection: choose the polarity with more detected reps
    if len(reps_raw_2) > len(reps_raw_1):
        reps_raw = reps_raw_2
        rep_debug = {**debug_2, "signal_inverted": True}
    else:
        reps_raw = reps_raw_1
        rep_debug = {**debug_1, "signal_inverted": False}

    analysis = build_analysis_v1(exercise, fps, reps_raw, rep_debug)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return analysis


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True, choices=["bench", "deadlift", "squat", "curl"])
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=25.0)
    args = ap.parse_args()

    analysis = compute_rep_metrics_file(args.exercise, Path(args.jsonl), Path(args.out), args.fps)
    print(f"[OK] wrote {args.out} ({analysis['set_summary_v1']['n_reps']} reps)")


if __name__ == "__main__":
    main()
