from typing import Dict, Any


def _f(rep: Dict[str, Any], *keys, default: float = 0.0) -> float:
    """Safely extract a float from rep dict."""
    for k in keys:
        if k in rep and rep[k] is not None:
            try:
                return float(rep[k])
            except:
                continue
    return float(default)


def analyze_rep(rep_index: int, rep: Dict[str, Any],
                avg_rom: float, avg_duration: float) -> Dict[str, Any]:
    """
    BENCH PRESS RULES (Version 1)
    Uses ROM + duration + top/bottom consistency heuristics.
    """

    rom = _f(rep, "rom", "amplitude")
    dur = _f(rep, "duration_sec", "duration")

    notes = []

    # --- ROM (depth + lockout) ---
    if rom < 0.02:
        notes.append("ROM is very short; aim for a full chest touch and full lockout.")
    elif rom < 0.035:
        notes.append("ROM slightly short; try lowering the bar a bit deeper.")
    else:
        notes.append("Good ROM on this rep.")

    # --- Tempo (eccentric control) ---
    if dur > 0:
        if dur < 0.7:
            notes.append("Rep is rushed; slow the eccentric and control the bar.")
        elif dur > 2.5:
            notes.append("Very slow grind; weight may be slightly heavy.")
        else:
            notes.append("Tempo looks controlled.")

    # --- Quality grade ---
    if rom >= 0.035 and 0.7 <= dur <= 2.5:
        quality = "good"
    elif rom >= 0.025:
        quality = "ok"
    else:
        quality = "needs_tweak"

    return {
        "quality": quality,
        "message": " ".join(notes)
    }
