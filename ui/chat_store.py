from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THREADS_DIR = Path("data/chats")
SCHEMA_VERSION = 3


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_thread_id(exercise: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
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


def _path_exists(raw: Any) -> bool:
    return bool(raw) and Path(str(raw)).exists()


def _canonical_exercise_from_record(data: dict[str, Any]) -> str:
    identity = data.get("analysis_identity") if isinstance(data.get("analysis_identity"), dict) else {}
    snapshot = data.get("analysis_snapshot") if isinstance(data.get("analysis_snapshot"), dict) else {}
    for candidate in (
        identity.get("exercise_canonical"),
        snapshot.get("exercise"),
        data.get("exercise"),
    ):
        if isinstance(candidate, str) and candidate:
            return candidate
    return "bench"


def _compact_analysis_snapshot(analysis: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(analysis, dict):
        return None
    summary = analysis.get("set_summary_v1") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "exercise": analysis.get("exercise"),
        "timestamp": analysis.get("timestamp"),
        "set_summary_v1": {
            "n_reps": summary.get("n_reps"),
            "avg_rom": summary.get("avg_rom"),
            "n_low_confidence": summary.get("n_low_confidence"),
            "quality_score": summary.get("quality_score") or summary.get("quality_score_pct"),
            "top_faults": summary.get("top_faults", []),
        },
    }


def _compact_response_snapshot(response: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(response, dict):
        return None
    structured = response.get("structured") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "response_text": response.get("response_text", ""),
        "structured": {
            "overall_score": structured.get("overall_score"),
            "faults": structured.get("faults", []),
            "coaching_cues": structured.get("coaching_cues", []),
        },
    }


def _build_analysis_ref(analysis: dict[str, Any] | None) -> dict[str, str]:
    analysis = analysis if isinstance(analysis, dict) else {}
    artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}
    ref = {
        "analysis_json": artifacts.get("analysis_json"),
        "overlay_path": artifacts.get("overlay_path") or artifacts.get("overlay_video") or analysis.get("overlay_path"),
        "run_dir": artifacts.get("run_dir") or analysis.get("run_dir"),
    }
    return {k: str(v) for k, v in ref.items() if v}


def _build_analysis_identity(
    analysis: dict[str, Any] | None,
    ref: dict[str, str],
    canonical_exercise: str,
    created_at: str,
) -> dict[str, Any]:
    analysis = analysis if isinstance(analysis, dict) else {}
    return {
        "exercise_canonical": canonical_exercise,
        "analysis_schema_version": analysis.get("schema_version") or "analysis_v1",
        "analysis_json": ref.get("analysis_json"),
        "run_dir": ref.get("run_dir"),
        "overlay_path": ref.get("overlay_path"),
        "analyzed_at": analysis.get("timestamp") or created_at,
    }


def _artifact_status_for_record(data: dict[str, Any]) -> str:
    identity = data.get("analysis_identity") if isinstance(data.get("analysis_identity"), dict) else {}
    ref = data.get("analysis_ref") if isinstance(data.get("analysis_ref"), dict) else {}
    snapshot = data.get("analysis_snapshot")

    analysis_json = identity.get("analysis_json") or ref.get("analysis_json")
    overlay_path = identity.get("overlay_path") or ref.get("overlay_path")
    has_snapshot = isinstance(snapshot, dict)
    has_analysis_json = _path_exists(analysis_json)
    has_overlay = _path_exists(overlay_path)

    if has_analysis_json and has_overlay:
        return "full"
    if has_snapshot or has_analysis_json or has_overlay:
        return "snapshot_only"
    return "missing"


def _compute_restore_status(data: dict[str, Any]) -> str:
    artifact_status = _artifact_status_for_record(data)
    return {
        "full": "full",
        "snapshot_only": "partial",
        "missing": "missing",
    }.get(artifact_status, "missing")


def save_thread(thread_id: str | None) -> None:
    import streamlit as st

    if not thread_id:
        return

    analysis = st.session_state.get("last_analysis")
    history = st.session_state.get("history", [])
    canonical_exercise = (
        analysis.get("exercise")
        if isinstance(analysis, dict) and analysis.get("exercise")
        else st.session_state.get("exercise_choice", "bench")
    )

    created_at = st.session_state.get("thread_created_at") or now_iso()
    st.session_state.thread_created_at = created_at
    st.session_state.thread_title = thread_title(created_at, canonical_exercise)
    st.session_state.exercise_choice = canonical_exercise

    ref = _build_analysis_ref(analysis)
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "thread_id": thread_id,
        "title": st.session_state.get("thread_title", thread_title(created_at, canonical_exercise)),
        "exercise": canonical_exercise,
        "created_at": created_at,
        "updated_at": now_iso(),
        "history": history if isinstance(history, list) else [],
        "analysis_ref": ref,
        "analysis_identity": _build_analysis_identity(analysis, ref, canonical_exercise, created_at),
        "analysis_snapshot": _compact_analysis_snapshot(analysis),
        "response_snapshot": _compact_response_snapshot(st.session_state.get("last_response")),
    }
    record["artifact_status"] = _artifact_status_for_record(record)
    record["restore_status"] = _compute_restore_status(record)

    _thread_path(thread_id).write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def load_thread(thread_id: str) -> None:
    import streamlit as st

    path = _thread_path(thread_id)
    if not path.exists():
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    created_at = data.get("created_at", now_iso())
    canonical_exercise = _canonical_exercise_from_record(data)
    ref = data.get("analysis_ref") if isinstance(data.get("analysis_ref"), dict) else {}
    analysis_json = ref.get("analysis_json")
    snapshot = data.get("analysis_snapshot")

    st.session_state.thread_id = data.get("thread_id", thread_id)
    st.session_state.thread_created_at = created_at
    st.session_state.thread_title = thread_title(created_at, canonical_exercise)
    st.session_state.exercise_choice = canonical_exercise
    st.session_state.history = data.get("history", []) if isinstance(data.get("history"), list) else []
    st.session_state.coach_note_input = ""
    if "exercise_choice_label" in st.session_state:
        del st.session_state["exercise_choice_label"]
    if "uploaded_video" in st.session_state:
        del st.session_state["uploaded_video"]

    if analysis_json and Path(str(analysis_json)).exists():
        try:
            st.session_state.last_analysis = json.loads(Path(str(analysis_json)).read_text(encoding="utf-8"))
        except Exception:
            st.session_state.last_analysis = snapshot if isinstance(snapshot, dict) else _stub_analysis(data)
    elif isinstance(snapshot, dict):
        st.session_state.last_analysis = snapshot
    else:
        st.session_state.last_analysis = _stub_analysis(data)

    st.session_state.last_response = (
        data.get("response_snapshot") if isinstance(data.get("response_snapshot"), dict) else None
    )
    st.session_state.last_payload = None

    overlay_path = ref.get("overlay_path") or (
        data.get("analysis_identity", {}).get("overlay_path")
        if isinstance(data.get("analysis_identity"), dict)
        else None
    )
    if overlay_path:
        st.session_state.last_analysis = st.session_state.last_analysis or {}
        st.session_state.last_analysis["overlay_path"] = overlay_path
        st.session_state.last_analysis.setdefault("artifacts_v1", {})["overlay_path"] = overlay_path

    if isinstance(st.session_state.last_analysis, dict):
        st.session_state.last_analysis.setdefault("exercise", canonical_exercise)

    st.session_state.restore_status = _compute_restore_status(data)
    st.session_state.ui_busy = False
    st.session_state.ui_message = None


def _stub_analysis(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "exercise": _canonical_exercise_from_record(data),
        "artifacts_v1": data.get("analysis_ref", {}),
        "_stub": True,
    }


def list_threads() -> list[dict[str, Any]]:
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    threads: list[dict[str, Any]] = []
    for p in THREADS_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            created_at = data.get("created_at", "")
            exercise = _canonical_exercise_from_record(data)
            threads.append(
                {
                    "thread_id": data.get("thread_id", p.stem),
                    "title": thread_title(created_at, exercise) if created_at else data.get("title", p.stem),
                    "exercise": exercise,
                    "artifact_status": _artifact_status_for_record(data),
                    "restore_status": _compute_restore_status(data),
                    "updated_at": data.get("updated_at", ""),
                }
            )
        except Exception:
            threads.append(
                {
                    "thread_id": p.stem,
                    "title": p.stem,
                    "exercise": "bench",
                    "artifact_status": "missing",
                    "restore_status": "missing",
                    "updated_at": "",
                }
            )
    threads.sort(key=lambda row: row.get("updated_at", ""), reverse=True)
    return threads
