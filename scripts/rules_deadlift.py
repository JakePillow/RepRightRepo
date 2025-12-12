from typing import Dict, Any


def _get_float(rep: Dict[str, Any], *keys, default: float = 0.0) -> float:
    for k in keys:
        if k in rep and rep[k] is not None:
            try:
                return float(rep[k])
            except (TypeError, ValueError):
                continue
    return float(default)


def analyze_rep(rep_index: int, rep: Dict[str, Any],
                avg_rom: float, avg_duration: float) -> Dict[str, Any]:
    """
    Very first version of deadlift-specific coaching.
    Uses only ROM + duration for now (no angles/bar path yet).
    """
    rom = _get_float(rep, "rom", "amplitude", default=0.0)
    dur = _get_float(rep, "duration_sec", "duration", default=0.0)

    notes = []

    # ROM cues
    if rom < 0.02:
        notes.append("ROM is very shallow; focus on fully locking out and returning to the floor with control.")
    elif rom < 0.04:
        notes.append("ROM is slightly short; try to finish each rep with full hip extension and stand tall.")
    else:
        notes.append("Good overall ROM on this rep.")

    # Tempo cues
    if dur > 0:
        if dur < 0.8:
            notes.append("Rep is quite fast; slow down the eccentric and avoid bouncing the bar.")
        elif dur > 2.5:
            notes.append("Very slow grind; if many reps feel like this, consider a small weight reduction.")
        else:
            notes.append("Tempo looks controlled for this rep.")

    # Simple quality label
    if rom >= 0.04 and 0.8 <= dur <= 2.5:
        quality = "good"
    elif rom >= 0.03:
        quality = "ok"
    else:
        quality = "needs_tweak"

    msg = " ".join(notes)

    return {
        "quality": quality,
        "message": msg,
    }
