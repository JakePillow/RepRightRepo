from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from repright.summary_v1 import build_set_summary_v1


def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _select_curl_side(left: list[float], right: list[float]) -> tuple[str, dict[str, Any]]:
    """Choose curl side with explicit quality rule.

    Rule priority:
    1) Higher valid sample count.
    2) Larger smoothed ROM over clip.
    3) Larger raw ROM.
    4) Deterministic tiebreak: right.
    """

    def _quality(vals: list[float]) -> dict[str, float]:
        if not vals:
            return {"valid_count": 0.0, "rom_smooth": 0.0, "rom_raw": 0.0}
        vals_s = smooth(vals, win=5)
        rom_raw = max(vals) - min(vals)
        rom_smooth = (max(vals_s) - min(vals_s)) if vals_s else 0.0
        return {
            "valid_count": float(len(vals)),
            "rom_smooth": float(rom_smooth),
            "rom_raw": float(rom_raw),
        }

    ql = _quality(left)
    qr = _quality(right)

    if ql["valid_count"] > qr["valid_count"]:
        selected = "left"
    elif qr["valid_count"] > ql["valid_count"]:
        selected = "right"
    elif ql["rom_smooth"] > qr["rom_smooth"]:
        selected = "left"
    elif qr["rom_smooth"] > ql["rom_smooth"]:
        selected = "right"
    elif ql["rom_raw"] > qr["rom_raw"]:
        selected = "left"
    else:
        selected = "right"

    return selected, {"left": ql, "right": qr}


def read_driver_angle(jsonl_path: Path, exercise: str) -> tuple[list[int], list[float], dict[str, Any]]:
    frames: list[int] = []
    driver_angles: list[float] = []
    left_angles: list[float] = []
    right_angles: list[float] = []

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            frame_v = _safe_float(row.get("frame"))
            if frame_v is None:
                continue
            frame_i = int(frame_v)

            angles_d = row.get("angles") or {}
            if exercise == "curl":
                l = _safe_float(angles_d.get("driver_left"))
                r = _safe_float(angles_d.get("driver_right"))
                d = _safe_float(angles_d.get("driver"))
                if l is not None:
                    left_angles.append(l)
                if r is not None:
                    right_angles.append(r)
                # keep per-frame fallback path for backward compatibility
                if l is None and r is None and d is not None:
                    frames.append(frame_i)
                    driver_angles.append(d)
            else:
                d = _safe_float(angles_d.get("driver"))
                if d is not None:
                    frames.append(frame_i)
                    driver_angles.append(d)

    if exercise != "curl":
        return frames, driver_angles, {"driver_selected": "driver"}

    # Curl: if bilateral channels exist, select best side clip-wise.
    if left_angles or right_angles:
        selected, quality = _select_curl_side(left_angles, right_angles)
        selected_key = "driver_left" if selected == "left" else "driver_right"

        # Re-read for frame-aligned selected-side series.
        frames = []
        driver_angles = []
        with jsonl_path.open("r", encoding="utf-8") as f2:
            for line in f2:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                frame_v = _safe_float(row.get("frame"))
                if frame_v is None:
                    continue
                angles_d = row.get("angles") or {}
                v = _safe_float(angles_d.get(selected_key))
                if v is None:
                    continue
                frames.append(int(frame_v))
                driver_angles.append(v)

        meta = {
            "driver_selected": selected_key,
            "driver_side_selected": selected,
            "driver_side_quality": quality,
            "driver_selection_rule": "valid_count > smoothed_rom > raw_rom > right_tiebreak",
        }
        return frames, driver_angles, meta

    # Legacy fallback: only single driver present.
    return frames, driver_angles, {
        "driver_selected": "driver",
        "driver_side_selected": "legacy_single",
        "driver_selection_rule": "fallback_single_driver",
    }


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
    collect_trace: bool = False,
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

    # Optional diagnostics for curl-only troubleshooting.
    trace_events: list[dict[str, Any]] = []
    max_trace_events = 300
    reject_counts = {
        "gap_too_short": 0,
        "duration": 0,
        "rom": 0,
        "duration_and_rom": 0,
        "accepted": 0,
    }
    transition_counts = {
        "top_to_down": 0,
        "down_to_up": 0,
        "up_to_top": 0,
    }

    def _trace(evt: dict[str, Any]) -> None:
        if collect_trace and len(trace_events) < max_trace_events:
            trace_events.append(evt)

    for i in range(1, len(a)):
        prev, cur = a[i - 1], a[i]

        if state == "top":
            if prev > high_enter and cur <= high_enter:
                f0cand = frames[i]
                if last_start_frame is not None and (f0cand - last_start_frame) / fps < min_gap_sec:
                    reject_counts["gap_too_short"] += 1
                    _trace({
                        "type": "start_rejected_gap",
                        "i": i,
                        "frame": int(f0cand),
                        "delta_sec": float((f0cand - last_start_frame) / fps),
                        "min_gap_sec": float(min_gap_sec),
                    })
                    continue
                state = "down"
                start_i = i
                peak_i = None
                last_start_frame = frames[i]
                transition_counts["top_to_down"] += 1
                _trace({"type": "top_to_down", "i": i, "frame": int(frames[i]), "angle": float(cur)})

        elif state == "down":
            if peak_i is None or cur < a[peak_i]:
                peak_i = i
                _trace({"type": "trough_update", "i": i, "frame": int(frames[i]), "angle": float(cur)})
            if prev < low_enter and cur >= low_enter:
                state = "up"
                transition_counts["down_to_up"] += 1
                _trace({"type": "down_to_up", "i": i, "frame": int(frames[i]), "angle": float(cur)})

        elif state == "up":
            if prev < high_exit and cur >= high_exit and start_i is not None and peak_i is not None:
                end_i = i
                f0, fp, f1 = frames[start_i], frames[peak_i], frames[end_i]
                dur = (f1 - f0) / fps
                seg = a[start_i : end_i + 1]
                rom_deg = float(max(seg) - min(seg))

                duration_ok = dur >= min_rep_duration_sec
                rom_ok = rom_deg >= min_rom_deg

                if duration_ok and rom_ok:
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
                    reject_counts["accepted"] += 1
                    _trace({
                        "type": "rep_accepted",
                        "start_frame": int(f0),
                        "peak_frame": int(fp),
                        "end_frame": int(f1),
                        "duration_sec": float(dur),
                        "rom_deg": float(rom_deg),
                    })
                else:
                    if (not duration_ok) and (not rom_ok):
                        reject_counts["duration_and_rom"] += 1
                        rej_reason = "duration_and_rom"
                    elif not duration_ok:
                        reject_counts["duration"] += 1
                        rej_reason = "duration"
                    else:
                        reject_counts["rom"] += 1
                        rej_reason = "rom"
                    _trace({
                        "type": "rep_rejected",
                        "reason": rej_reason,
                        "start_frame": int(f0),
                        "peak_frame": int(fp),
                        "end_frame": int(f1),
                        "duration_sec": float(dur),
                        "rom_deg": float(rom_deg),
                        "min_rep_duration_sec": float(min_rep_duration_sec),
                        "min_rom_deg": float(min_rom_deg),
                    })

                state = "top"
                start_i = None
                peak_i = None
                transition_counts["up_to_top"] += 1

    debug = {
        "signal_min": float(amin),
        "signal_max": float(amax),
        "rom_total": float(rom_total),
        "threshold_low": float(low),
        "threshold_high": float(high),
        "min_rom_deg": float(min_rom_deg),
        "min_rep_duration_sec": float(min_rep_duration_sec),
        "fps": float(fps),
        "state_transition_counts": transition_counts,
        "rejection_counts": reject_counts,
        "unfinished_cycle_state": state,
        "unfinished_cycle_has_start": bool(start_i is not None),
        "unfinished_cycle_has_trough": bool(peak_i is not None),
    }
    if collect_trace:
        debug["trace_events"] = trace_events
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

    if exercise == "bench" and rep["rom"] < 0.35:
        faults.append(
            _make_fault(
                code="LOW_ROM",
                severity="warn" if rep["rom"] >= 0.2 else "error",
                value=rep["rom"],
                threshold=0.35,
                evidence="Normalized ROM below threshold.",
            )
        )

    biomech = rep.get("biomech_v1") or {}
    driver_rom_deg = biomech.get("driver_rom_deg")

    if exercise == "bench":
        if driver_rom_deg is not None and float(driver_rom_deg) < 75.0:
            faults.append(
                _make_fault(
                    code="WEAK_EXTENSION",
                    severity="warn",
                    value=float(driver_rom_deg),
                    threshold=75.0,
                    evidence="Peak extension proxy remained below lockout threshold.",
                )
            )

    if exercise == "squat":
        if rep["rom"] < 0.35:
            faults.append(
                _make_fault(
                    code="INSUFFICIENT_DEPTH",
                    severity="error" if rep["rom"] < 0.2 else "warn",
                    value=rep["rom"],
                    threshold=0.35,
                    evidence="Normalized squat ROM did not reach depth threshold.",
                )
            )
        if (
            driver_rom_deg is not None
            and float(driver_rom_deg) > 65.0
            and rep["rom"] >= 0.3
        ):
            faults.append(
                _make_fault(
                    code="FORWARD_LEAN",
                    severity="warn",
                    value=float(driver_rom_deg),
                    threshold=65.0,
                    evidence="Trunk proxy angle change exceeded threshold, suggesting forward lean. Used as proxy due to monocular pose estimation limitations.",
                )
            )

    if exercise == "deadlift":
        if rep["rom"] < 0.5:
            faults.append(
                _make_fault(
                    code="LOW_ROM",
                    severity="warn",
                    value=rep["rom"],
                    threshold=0.5,
                    evidence="Bar path suggests incomplete lift.",
                )
            )

    if exercise == "curl":
        momentum_swing = rep["tempo_up_sec"] < 0.30 and (rep["rom"] < 0.78 or rep["tempo_down_sec"] < 0.45)
        if momentum_swing:
            faults.append(
                _make_fault(
                    code="MOMENTUM_SWING",
                    severity="warn",
                    value=rep["tempo_up_sec"],
                    threshold=0.30,
                    evidence="Very short concentric with shallow ROM or fast eccentric suggests momentum-assisted swing. Used as proxy due to monocular pose estimation limitations.",
                )
            )
        if rep["rom"] < 0.2:
            faults.append(
                _make_fault(
                    code="INCOMPLETE_EXTENSION",
                    severity="error" if rep["rom"] < 0.1 else "warn",
                    value=rep["rom"],
                    threshold=0.2,
                    evidence="Normalized ROM below extension threshold indicates incomplete extension.",
                )
            )
    return faults


def build_analysis_v1(exercise: str, fps: float, reps_raw: list[dict[str, Any]], rep_debug: dict[str, Any]) -> dict[str, Any]:
    rep_debug = dict(rep_debug or {})
    rep_debug.setdefault("thresholds", {
        "global": {},
        "bench": {
            "LOW_ROM_rom_lt": 0.35,
            "WEAK_EXTENSION_driver_rom_deg_lt": 75.0,
        },
        "curl": {
            "MOMENTUM_SWING_tempo_up_sec_lt": 0.30,
            "MOMENTUM_SWING_rom_lt": 0.78,
            "MOMENTUM_SWING_tempo_down_sec_lt": 0.45,
            "INCOMPLETE_EXTENSION_rom_lt": 0.2,
        },
        "squat": {
            "INSUFFICIENT_DEPTH_rom_lt": 0.35,
            "FORWARD_LEAN_driver_rom_deg_gt": 65.0,
            "FORWARD_LEAN_min_rom": 0.3,
        },
        "deadlift": {
            "LOW_ROM_rom_lt": 0.5,
        },
    })
    rep_debug.setdefault(
        "signal_stats",
        {
            "signal_min": rep_debug.get("signal_min"),
            "signal_max": rep_debug.get("signal_max"),
            "rom_total": rep_debug.get("rom_total"),
            "fps": fps,
        },
    )
    rep_debug.setdefault("rejection_counts", rep_debug.get("rejection_counts") or {})

    reps: list[dict[str, Any]] = []
    for idx, r in enumerate(reps_raw, start=1):
        _DRIVER_MAP = {
            "bench":    "elbow",
            "curl":     "elbow",
            "squat":    "trunk_proxy",
            "deadlift": "hip_y",      # hip height rises to lockout — peak = completed rep
        }
        driver = _DRIVER_MAP.get(exercise, "trunk_proxy")
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
    rep_debug["rep_count_detected"] = int(len(reps))
    if len(reps) == 0:
        rep_debug.setdefault("failure_reason", "no_valid_rep_detected")

    return {
        "schema_version": "analysis_v1",
        "exercise": exercise,
        "fps": fps,
        "driver_signal": rep_debug.get("driver_selected") or rep_debug.get("driver_signal"),
        "driver_side": rep_debug.get("driver_side_selected"),
        "reps": reps,
        "set_summary_v1": set_summary,
        "rep_debug": rep_debug,
    }


def compute_rep_metrics_file(
    exercise: str,
    jsonl_path: Path,
    out_path: Path,
    fps: float = 25.0,
    curl_diag: bool = False,
) -> dict[str, Any]:
    frames, angles, driver_meta = read_driver_angle(jsonl_path, exercise)

    a_s = smooth(angles, win=5)

    detect_kwargs: dict[str, float] = {}
    curl_diag_enabled = exercise == "curl" and os.getenv("REPRIGHT_CURL_DIAG", "0").strip().lower() in {"1", "true", "yes", "on"}
    if exercise == "curl":
        detect_kwargs = {
            "min_rom_deg": 9.0,
            "min_rep_duration_sec": 0.35,
            "min_gap_sec": 0.45,
        }

    # Run detection on normal signal
    reps_raw_1, debug_1 = detect_reps(frames, a_s, fps, collect_trace=curl_diag_enabled, **detect_kwargs)

    # Run detection on inverted signal (polarity robustness)
    a_inv = [-v for v in a_s]
    reps_raw_2, debug_2 = detect_reps(frames, a_inv, fps, collect_trace=curl_diag_enabled, **detect_kwargs)

    # Deterministic selection: choose the polarity with more detected reps
    if len(reps_raw_2) > len(reps_raw_1):
        reps_raw = reps_raw_2
        rep_debug = {**debug_2, **driver_meta, "signal_inverted": True}
    else:
        reps_raw = reps_raw_1
        rep_debug = {**debug_1, **driver_meta, "signal_inverted": False}

    analysis = build_analysis_v1(exercise, fps, reps_raw, rep_debug)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    if curl_diag_enabled:
        diag = {
            "exercise": exercise,
            "jsonl": str(jsonl_path),
            "driver_signal": "angles.driver (RIGHT_SHOULDER-RIGHT_ELBOW-RIGHT_WRIST elbow angle)",
            "signal_summary": {
                "frames": int(len(frames)),
                "raw_min": float(min(angles)) if angles else None,
                "raw_max": float(max(angles)) if angles else None,
                "raw_rom_total": float((max(angles) - min(angles))) if angles else None,
                "smoothed_min": float(min(a_s)) if a_s else None,
                "smoothed_max": float(max(a_s)) if a_s else None,
                "smoothed_rom_total": float((max(a_s) - min(a_s))) if a_s else None,
            },
            "params": detect_kwargs,
            "normal": debug_1,
            "inverted": debug_2,
            "selected_polarity": "inverted" if rep_debug.get("signal_inverted") else "normal",
            "selected_n_reps": int(len(reps_raw)),
        }
        diag_path = out_path.with_name(f"{out_path.stem}.curl_diag.json")
        diag_path.write_text(json.dumps(diag, indent=2), encoding="utf-8")
        print(f"[DIAG] wrote {diag_path}")

    return analysis


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True, choices=["bench", "deadlift", "squat", "curl"])
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument(
        "--curl-diag",
        action="store_true",
        help="Enable curl-only diagnostics (writes <out>.curl_diag.json).",
    )
    args = ap.parse_args()

    analysis = compute_rep_metrics_file(args.exercise, Path(args.jsonl), Path(args.out), args.fps, curl_diag=args.curl_diag)
    print(f"[OK] wrote {args.out} ({analysis['set_summary_v1']['n_reps']} reps)")


if __name__ == "__main__":
    main()

