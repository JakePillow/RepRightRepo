from __future__ import annotations

from typing import Any


VALID_SEVERITIES = {"info", "warn", "error"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "exercise",
    "driver_signal",
    "reps",
    "set_summary_v1",
    "timestamp",
    "video_id",
}


def validate_analysis(analysis: dict[str, Any]) -> None:
    if not isinstance(analysis, dict):
        raise ValueError("analysis must be a dict")

    missing = sorted(k for k in REQUIRED_TOP_LEVEL if k not in analysis)
    if missing:
        raise ValueError(f"analysis missing required fields: {', '.join(missing)}")

    reps = analysis.get("reps")
    if not isinstance(reps, list):
        raise ValueError("analysis.reps must be a list")

    set_summary = analysis.get("set_summary_v1")
    if not isinstance(set_summary, dict):
        raise ValueError("analysis.set_summary_v1 must be a dict")

    expected_index = 1
    for rep in reps:
        if not isinstance(rep, dict):
            raise ValueError("analysis.reps items must be dicts")

        for key in ("rep_index", "start_frame", "peak_frame", "end_frame"):
            if key not in rep:
                raise ValueError(f"rep missing required field: {key}")

        if rep.get("rep_index") != expected_index:
            raise ValueError("rep_index values must be sequential starting at 1")

        faults = rep.get("faults_v1") or []
        if not isinstance(faults, list):
            raise ValueError("rep.faults_v1 must be a list")

        for fault in faults:
            if not isinstance(fault, dict):
                raise ValueError("fault entries must be dicts")
            severity = fault.get("severity")
            if severity not in VALID_SEVERITIES:
                raise ValueError(f"invalid fault severity: {severity}")

        expected_index += 1
