from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from repright.schema.analysis_v1 import SetSummaryV1


def _mean(xs: List[float]) -> float:
    xs2 = [float(x) for x in xs if x is not None]
    return float(sum(xs2) / len(xs2)) if xs2 else 0.0


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
    }
    return out
