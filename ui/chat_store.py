from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THREADS_DIR   = Path("data/chats")
SCHEMA_VERSION = 2

# ── Helpers ───────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_thread_id(exercise: str) -> str:
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    uid  = uuid.uuid4().hex[:6]
    return f"{ts}_{exercise}_{uid}"


def thread_title(created_at: str, exercise: str) -> str:
    try:
        dt = datetime.fromisoformat(created_at)
        return f"{dt.strftime('%Y-%m-%d')} – {exercise}"
    except Exception:
        return f"{created_at[:10]} – {exercise}"


def _thread_path(thread_id: str) -> Path:
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    return THREADS_DIR / f"{thread_id}.json"


# ── Snapshot helpers ──────────────────────────────────────────

def _compact_analysis_snapshot(analysis: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Extract the normalised, self-contained fields that power the UI.
    Does NOT store file paths — only primitive values.
    """
    if not isinstance(analysis, dict):
        return None
    summary = analysis.get("set_summary_v1") or {}
    return {
        "schema_version":  SCHEMA_VERSION,
        "exercise":        analysis.get("exercise"),
        "set_summary_v1": {
            "n_reps":           summary.get("n_reps"),
            "avg_rom":          summary.get("avg_rom"),
            "n_low_confidence": summary.get("n_low_confidence"),
            "quality_score":    summary.get("quality_score")
                                or summary.get("quality_score_pct"),
            "top_faults":       summary.get("top_faults", []),
        },
    }


def _compact_response_snapshot(response: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(response, dict):
        return None
    structured = response.get("structured") or {}
    return {
        "schema_version":  SCHEMA_VERSION,
        "response_text":   response.get("response_text", ""),
        "structured": {
            "overall_score": structured.get("overall_score"),
            "faults":        structured.get("faults", []),
            "coaching_cues": structured.get("coaching_cues", []),
        },
    }


def _compact_payload_snapshot(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    comparison = payload.get("comparison_v1")
    if not isinstance(comparison, dict):
        return None
    return {
        "schema_version": SCHEMA_VERSION,
        "comparison_v1": comparison,
    }


# ── Restore-status detection ──────────────────────────────────

def _compute_restore_status(data: dict[str, Any]) -> str:
    """
    Returns 'full', 'partial', or 'missing'.
    - full:    embedded snapshot present and complete
    - partial: snapshot present but missing some fields, or only file refs remain
    - missing: no snapshot and no resolvable file refs
    """
    snap = data.get("analysis_snapshot")
    if isinstance(snap, dict):
        summary = snap.get("set_summary_v1") or {}
        if summary.get("quality_score") is not None and summary.get("n_reps") is not None:
            return "full"
        return "partial"

    # Legacy: try file refs
    ref = data.get("analysis_ref") or {}
    apath = ref.get("analysis_json")
    if apath and Path(str(apath)).exists():
        return "partial"

    return "missing"


# ── Public API ────────────────────────────────────────────────

def save_thread(thread_id: str) -> None:
    import streamlit as st
    if not thread_id:
        return
    path    = _thread_path(thread_id)
    history = st.session_state.get("history", [])

    # Build artifact refs (file pointers — kept for overlay lookup)
    analysis = st.session_state.get("last_analysis") or {}
    payload  = st.session_state.get("last_payload")  or {}
    canonical_exercise = analysis.get("exercise") or st.session_state.get("exercise_choice", "bench")
    created_at = st.session_state.get("thread_created_at", now_iso())
    artifacts = analysis.get("artifacts_v1") or {}
    ref = {
        k: str(v)
        for k, v in {
            "analysis_json": artifacts.get("analysis_json"),
            "overlay_path":  artifacts.get("overlay_path")
                             or artifacts.get("overlay_video")
                             or analysis.get("overlay_path"),
            "run_dir":       artifacts.get("run_dir") or analysis.get("run_dir"),
        }.items()
        if v
    }

    # Embed canonical snapshots
    analysis_snap = _compact_analysis_snapshot(
        st.session_state.get("last_analysis"))
    response_snap = _compact_response_snapshot(
        st.session_state.get("last_response"))
    payload_snap = _compact_payload_snapshot(
        st.session_state.get("last_payload"))

    record: dict[str, Any] = {
        "schema_version":    SCHEMA_VERSION,
        "thread_id":         thread_id,
        "title":             st.session_state.get("thread_title") or thread_title(created_at, canonical_exercise),
        "exercise":          canonical_exercise,
        "load_kg":           st.session_state.get("last_analysis_load_kg"),
        "created_at":        created_at,
        "updated_at":        now_iso(),
        "history":           history,
        "analysis_ref":      ref,
        "analysis_snapshot": analysis_snap,
        "response_snapshot": response_snap,
        "payload_snapshot":  payload_snap,
    }
    record["restore_status"] = _compute_restore_status(record)
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def load_thread(thread_id: str) -> None:
    import streamlit as st
    path = _thread_path(thread_id)
    if not path.exists():
        return

    data = json.loads(path.read_text(encoding="utf-8"))

    st.session_state.thread_id         = thread_id
    st.session_state.thread_title      = data.get("title", thread_id)
    st.session_state.thread_created_at = data.get("created_at", now_iso())
    st.session_state.exercise_choice   = data.get("exercise", "bench")
    st.session_state.ui_load_kg        = data.get("load_kg") or 0.0
    st.session_state.last_analysis_load_kg = data.get("load_kg")
    st.session_state.history           = data.get("history", [])

    # ── Restore analysis from snapshot (preferred) or file ref (fallback) ──
    snap = data.get("analysis_snapshot")
    if isinstance(snap, dict):
        st.session_state.last_analysis = snap
    else:
        ref   = data.get("analysis_ref") or {}
        apath = ref.get("analysis_json")
        if apath and Path(str(apath)).exists():
            try:
                st.session_state.last_analysis = json.loads(
                    Path(str(apath)).read_text(encoding="utf-8"))
            except Exception:
                st.session_state.last_analysis = _stub_analysis(data)
        else:
            st.session_state.last_analysis = _stub_analysis(data)

    # ── Restore coaching response from snapshot ──
    rsnap = data.get("response_snapshot")
    st.session_state.last_response = rsnap if isinstance(rsnap, dict) else None
    psnap = data.get("payload_snapshot")
    st.session_state.last_payload = psnap if isinstance(psnap, dict) else None

    # ── Restore overlay path (file ref only — bytes stay on disk) ──
    ref  = data.get("analysis_ref") or {}
    op   = ref.get("overlay_path")
    if op and Path(str(op)).exists():
        if "artifacts_v1" not in (st.session_state.last_analysis or {}):
            st.session_state.last_analysis = st.session_state.last_analysis or {}
            st.session_state.last_analysis.setdefault("artifacts_v1", {})["overlay_path"] = op

    # ── Store restore status for UI callout ──
    st.session_state.restore_status = _compute_restore_status(data)


def _stub_analysis(data: dict[str, Any]) -> dict[str, Any]:
    """Minimal stub so the UI does not crash on legacy/corrupt threads."""
    return {
        "exercise":      data.get("exercise", "bench"),
        "artifacts_v1":  data.get("analysis_ref", {}),
        "_stub":         True,
    }


def list_threads() -> list[dict[str, Any]]:
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    threads: list[dict[str, Any]] = []
    for p in sorted(THREADS_DIR.glob("*.json"), reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            threads.append({
                "thread_id":      d.get("thread_id", p.stem),
                "title":          d.get("title", p.stem),
                "restore_status": d.get("restore_status", "unknown"),
                "updated_at":     d.get("updated_at", ""),
            })
        except Exception:
            threads.append({"thread_id": p.stem, "title": p.stem,
                            "restore_status": "missing", "updated_at": ""})
    return threads
