from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from repright.schema.analysis_v1 import SetSummaryV1


def _mean(xs: List[float]) -> float:
    xs2 = [float(x) for x in xs if x is not None]
    return float(sum(xs2) / len(xs2)) if xs2 else 0.0




def _quality_score_and_band(reps: List[Dict[str, Any]]) -> Tuple[int, str]:
    score = 100
    sev_penalty = {"high": 15, "error": 15, "medium": 8, "warn": 8, "low": 4, "info": 4}
    conf_penalty = {"medium": 8, "low": 15}

    for r in reps:
        conf = r.get("confidence_v1") or {}
        level = str(conf.get("level") or "").lower()
        score -= conf_penalty.get(level, 0)

        for f in (r.get("faults_v1") or []):
            sev = str((f or {}).get("severity") or "info").lower()
            score -= sev_penalty.get(sev, 4)

    # consistency penalties (if enough reps)
    roms = [float(r.get("rom")) for r in reps if isinstance(r.get("rom"), (int, float))]
    ups = [float(r.get("tempo_up_sec")) for r in reps if isinstance(r.get("tempo_up_sec"), (int, float))]
    downs = [float(r.get("tempo_down_sec")) for r in reps if isinstance(r.get("tempo_down_sec"), (int, float))]

    def _std(xs: List[float]) -> float:
        if len(xs) < 2:
            return 0.0
        m = sum(xs) / len(xs)
        return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5

    if _std(roms) > 0.10:
        score -= 8
    if _std(ups) > 0.25:
        score -= 6
    if _std(downs) > 0.25:
        score -= 6

    score = max(0, min(100, int(round(score))))
    if score >= 80:
        band = "green"
    elif score >= 50:
        band = "yellow"
    else:
        band = "red"
    return score, band

def build_set_summary_v1(reps: List[Dict[str, Any]]) -> SetSummaryV1:
    """
    Build a stable set-level summary from per-rep metrics.
    This is purely architectural: no rep detection logic lives here.
    """
    n = int(len(reps))

    roms = [r.get("rom", 0.0) for r in reps]
    durs = [r.get("duration_sec", 0.0) for r in reps]
    ups  = [r.get("tempo_up_sec", 0.0) for r in reps]
    downs = [r.get("tempo_down_sec", 0.0) for r in reps]

    n_low_conf = 0
    n_inferred = 0

    fault_counts = Counter()
    severity_rank = {"info": 1, "warn": 2, "error": 3}

    # track max severity seen per fault code
    fault_sev_max: Dict[str, str] = {}

    for r in reps:
        conf = r.get("confidence_v1") or {}
        level = (conf.get("level") or "high").lower()
        if level in ("medium", "low"):
            n_low_conf += 1

        if bool(r.get("tempo_down_inferred", False)):
            n_inferred += 1

        for f in (r.get("faults_v1") or []):
            code = str(f.get("code", "") or "")
            if not code:
                continue
            fault_counts[code] += 1

            sev = str(f.get("severity", "info") or "info").lower()
            prev = fault_sev_max.get(code)
            if prev is None:
                fault_sev_max[code] = sev
            else:
                if severity_rank.get(sev, 1) > severity_rank.get(prev, 1):
                    fault_sev_max[code] = sev

    top_faults = []
    for code, cnt in fault_counts.most_common(8):
        top_faults.append({
            "code": code,
            "count": int(cnt),
            "severity_max": fault_sev_max.get(code, "info"),
        })

    quality_score, quality_band = _quality_score_and_band(reps)

    out: SetSummaryV1 = {
        "n_reps": n,
        "avg_rom": _mean(roms),
        "avg_duration_sec": _mean(durs),
        "avg_tempo_up_sec": _mean(ups),
        "avg_tempo_down_sec": _mean(downs),
        "n_low_confidence": int(n_low_conf),
        "n_inferred_eccentric": int(n_inferred),
        "fault_counts": {k: int(v) for k, v in fault_counts.items()},
        "top_faults": top_faults,
        "quality_score_pct": quality_score,
        "quality_band": quality_band,
    }
    return out
