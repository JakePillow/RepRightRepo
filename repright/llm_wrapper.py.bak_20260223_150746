# repright/llm_wrapper.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


# 1) Define allowed fault codes per exercise (minimal v1)
ALLOWED_FAULTS: Dict[str, set] = {
    "bench": {
        "TEMPO_FAST_ECCENTRIC",
        "PARTIAL_ROM",
        "HIP_LIFT",
        "SHOULDER_INSTABILITY",
        "ASYM_ROM_ELBOW",   # if you still want it for bench
    },
    "deadlift": {
        "TOO_FAST",
        "PARTIAL_ROM",
        "LUMBAR_FLEXION",
        "UPPER_BACK_ROUNDING",
        "TEMPO_FAST_ECCENTRIC",  # optional if you keep this generic code
    },
    "curl": {
        "TOO_FAST",
        "PARTIAL_ROM",
        "TORSO_SWING",
        "ELBOW_FLARE",
        "POOR_ECCENTRIC_CONTROL",
        "INCONSISTENT_TEMPO",
        "ASYMMETRIC_MOTION",
        "SHRUGGING",
    },
    "squat": {
        "TEMPO_ISSUE",
        "DEPTH_FAIL",
        "KNEE_VALGUS",
        "TRUNK_FLEXION",
        "PARTIAL_ROM",
        "TOO_FAST",
    },
}

# 2) Suggestion text keyed by (exercise, fault_code)
SUGGESTIONS: Dict[Tuple[str, str], str] = {
    # deadlift
    ("deadlift", "TOO_FAST"): "Slow the descent and reset between reps; avoid bouncing off the floor.",
    ("deadlift", "PARTIAL_ROM"): "Aim for full lockout: hips through, knees straight, stand tall at the top.",
    ("deadlift", "LUMBAR_FLEXION"): "Brace harder (big breath + belt/abs) and keep neutral lumbar; reduce load if you can’t maintain position.",
    ("deadlift", "UPPER_BACK_ROUNDING"): "Set lats (pull slack out of the bar) and keep chest proud; think ‘squeeze oranges in your armpits’.",

    # bench (examples; adapt to your eventual metrics)
    ("bench", "TEMPO_FAST_ECCENTRIC"): "Control the descent; aim ~0.5–1.0s down for repeatable touch point.",
    ("bench", "PARTIAL_ROM"): "Touch the same spot on your chest each rep, then full lockout without losing tightness.",
    ("bench", "HIP_LIFT"): "Keep glutes pinned; drive legs but don’t let hips pop off the bench.",
    ("bench", "SHOULDER_INSTABILITY"): "Retract/depress scapulae and keep shoulders packed; reduce load if shoulders shift.",

    # curl
    ("curl", "TORSO_SWING"): "Lock ribs down and curl without swinging; lighten load if you can’t keep torso still.",
    ("curl", "ELBOW_FLARE"): "Keep elbows slightly in front of the body and don’t let them drift wide.",
    ("curl", "POOR_ECCENTRIC_CONTROL"): "Own the negative; aim ~1–2s down.",
    ("curl", "INCONSISTENT_TEMPO"): "Use a consistent tempo across reps; avoid rushing the hard reps.",
    ("curl", "SHRUGGING"): "Keep shoulders down; don’t shrug up as you curl.",

    # squat
    ("squat", "DEPTH_FAIL"): "Hit consistent depth; reduce load or widen stance if you’re cutting it high.",
    ("squat", "KNEE_VALGUS"): "Drive knees out in line with toes; slow down and control the bottom.",
    ("squat", "TRUNK_FLEXION"): "Brace harder and keep chest up; reduce load if you fold at the bottom.",
    ("squat", "TEMPO_ISSUE"): "Control the descent and pause slightly if you’re dive-bombing.",
}


def _get(d: Dict[str, Any], path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _count_faults(rep_table: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rep_table or []:
        faults = r.get("faults") or r.get("faults_v1") or []
        for f in faults:
            if isinstance(f, dict):
                code = f.get("code")
                if code:
                    counts[code] = counts.get(code, 0) + 1
    return counts


def _tempo_down_range(rep_table: List[Dict[str, Any]]):
    vals = []
    for r in rep_table or []:
        v = r.get("tempo_down_sec")
        if v is None:
            v = r.get("tempo_down_sec_inferred")
        if isinstance(v, (int, float)):
            vals.append(float(v))
    if not vals:
        return None, None
    return min(vals), max(vals)


def build_stub_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    ex = (payload.get("exercise") or _get(payload, "analysis_v1.exercise") or "unknown").lower()
    load_kg = payload.get("load_kg")
    rep_table = payload.get("rep_table") or []

    counts = _count_faults(rep_table)
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

    tmin, tmax = _tempo_down_range(rep_table)
    overlay_path = _get(payload, "highlights.overlay_path") or _get(payload, "analysis_v1.overlay_path")
    metrics_path = _get(payload, "highlights.metrics_path") or _get(payload, "analysis_v1.metrics_path")

    # Guardrail: detect “exercise-mismatched” fault codes
    allowed = ALLOWED_FAULTS.get(ex, set())
    mismatched = [c for c in counts.keys() if allowed and c not in allowed]

    if isinstance(load_kg, (int, float)):
        header = f"{ex.title()} @ {float(load_kg):.1f}kg — quick take based on this set."
    else:
        header = f"{ex.title()} — quick take based on this set."

    lines = [header]
    lines.append(f"- Reps detected: {len(rep_table)}")

    if isinstance(tmin, (int, float)) and isinstance(tmax, (int, float)):
        lines.append(f"- Eccentric speed range: {tmin:.2f}s to {tmax:.2f}s")

    if top:
        top_str = ", ".join([f"{c}×{n}" for c, n in top[:5]])
        lines.append(f"- Top flags: {top_str}")
    else:
        lines.append("- Top flags: none")

    if mismatched:
        lines.append(f"WARNING: fault codes not allowed for {ex}: {', '.join(mismatched)}")

    lines.append("")
    lines.append("Suggestions:")

    # Only emit suggestions for faults actually present
    emitted = 0
    for code, _n in top:
        s = SUGGESTIONS.get((ex, code))
        if s:
            lines.append(f"- {s}")
            emitted += 1

    if emitted == 0:
        lines.append("- No exercise-specific flags detected from current metrics. (Need exercise-specific rules/metrics wiring.)")

    lines.append("- Tell me your goal (strength vs hypertrophy) and I’ll tailor cues.")

    return {
        "schema_version": "coach_response_v1",
        "mode": "stub",
        "response_text": "\n".join(lines),
        "debug": {
            "exercise": ex,
            "load_kg": load_kg,
            "fault_counts": counts,
            "tempo_down_sec_min": tmin,
            "tempo_down_sec_max": tmax,
            "overlay_path": overlay_path,
            "metrics_path": metrics_path,
            "mismatched_fault_codes": mismatched,
        },
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    out = build_stub_response(payload)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(args.out)
    print(out["response_text"])


if __name__ == "__main__":
    main()