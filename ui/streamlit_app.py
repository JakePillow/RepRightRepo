from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach

EXERCISES = ["bench", "deadlift", "squat", "curl"]
CHATS_DIR = ROOT / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_thread_id(exercise: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{exercise}"


def _thread_path(thread_id: str) -> Path:
    return CHATS_DIR / f"{thread_id}.json"


def _parse_ts(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min


def list_threads() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in CHATS_DIR.glob("*.json"):
        try:
            thread = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(thread, dict):
                out.append(thread)
        except Exception:
            continue
    out.sort(key=lambda t: _parse_ts(t.get("updated_at")), reverse=True)
    return out


def _thread_title(created_at: str | None, exercise: str | None) -> str:
    ex = exercise or "unknown"
    try:
        dt = datetime.fromisoformat(created_at or "")
        return f"{dt.strftime('%Y-%m-%d')} • {ex}"
    except ValueError:
        return f"{datetime.now().strftime('%Y-%m-%d')} • {ex}"


def _save_thread(thread_id: str) -> None:
    if not thread_id:
        return

    analysis = st.session_state.get("last_analysis") or {}
    artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}
    analysis_json = artifacts.get("analysis_json") or analysis.get("metrics_path")
    overlay_path = analysis.get("overlay_path") or artifacts.get("overlay_path")

    fallback_exercise = analysis.get("exercise") or st.session_state.get("exercise_choice") or thread_id.split("_")[-1]

    thread = {
        "thread_id": thread_id,
        "created_at": st.session_state.get("thread_created_at"),
        "updated_at": _now_iso(),
        "title": st.session_state.get("thread_title") or _thread_title(st.session_state.get("thread_created_at"), fallback_exercise),
        "exercise": fallback_exercise,
        "analysis_ref": {
            "analysis_json": analysis_json,
            "overlay_path": overlay_path,
            "run_dir": artifacts.get("run_dir"),
            "video_path": analysis.get("video_path"),
        },
        "history": st.session_state.get("history") or [],
    }

    _thread_path(thread_id).write_text(json.dumps(thread, indent=2), encoding="utf-8")


def _load_thread(thread_id: str) -> None:
    p = _thread_path(thread_id)
    if not p.exists():
        return

    thread = json.loads(p.read_text(encoding="utf-8"))
    analysis_ref = thread.get("analysis_ref") if isinstance(thread.get("analysis_ref"), dict) else {}

    st.session_state.thread_id = thread.get("thread_id")
    st.session_state.thread_created_at = thread.get("created_at")
    st.session_state.thread_title = thread.get("title")
    st.session_state.history = thread.get("history") if isinstance(thread.get("history"), list) else []

    analysis_json = analysis_ref.get("analysis_json")
    overlay_path = analysis_ref.get("overlay_path")

    loaded_analysis: dict[str, Any] | None = None
    if analysis_json:
        p_analysis = Path(str(analysis_json))
        if p_analysis.exists():
            try:
                loaded_analysis = json.loads(p_analysis.read_text(encoding="utf-8"))
            except Exception:
                loaded_analysis = None

    if loaded_analysis is None:
        loaded_analysis = {
            "exercise": thread.get("exercise"),
            "overlay_path": overlay_path,
            "artifacts_v1": {
                "analysis_json": analysis_json,
                "overlay_path": overlay_path,
                "run_dir": analysis_ref.get("run_dir"),
                "metrics_path": analysis_json,
            },
        }

    st.session_state.last_analysis = loaded_analysis
    st.session_state.last_payload = None
    st.session_state.last_response = None
    st.session_state.active_upload_sig = None
    st.session_state.pending_upload_sig = None


def _append_history(role: str, content: str) -> None:
    st.session_state.history.append({"role": role, "content": content, "ts": _now_iso()})


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Nunito', system-ui, sans-serif; }

        header[data-testid="stHeader"] { display: none; }
        div[data-testid="stToolbar"] { display: none; }
        div[data-testid="stDecoration"] { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container { padding-top: 1.2rem; }

        section[data-testid="stSidebar"][aria-expanded="false"] {
          min-width: 6rem !important;
          max-width: 6rem !important;
        }
        button[data-testid="collapsedControl"] {
          display: inline-flex !important;
          visibility: visible !important;
          opacity: 1 !important;
        }

        .rr-header {
          position: sticky;
          top: 0;
          z-index: 50;
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          backdrop-filter: blur(8px);
          border-radius: 16px;
          padding: 12px 16px;
          margin-bottom: 12px;
          text-align: center;
        }
        .rr-title { font-size: 1.4rem; font-weight: 800; }
        .rr-sub { opacity: 0.8; font-size: 0.95rem; }
        .rr-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 700; }
        .rr-ready { background: rgba(28,200,138,0.2); color: #66f1ba; }
        .rr-busy { background: rgba(255,185,0,0.2); color: #ffd66f; }

        .rr-card { border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.04); border-radius: 16px; padding: 12px; margin-bottom: 10px; }
        .thread-row button { width: 100%; text-align: left; }
        </style>
        """,
        unsafe_allow_html=True,
    )




def _upload_signature(upload) -> str:
    hasher = hashlib.md5()
    raw = upload.getvalue()
    hasher.update(raw[:1024 * 1024])
    return f"{upload.name}:{len(raw)}:{hasher.hexdigest()}"

def _safe_tmp_video(upload) -> Path:
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)
    p = Path(path)
    p.write_bytes(upload.getbuffer())
    return p


def _overlay_debug_candidates() -> list[Path]:
    payload = st.session_state.last_payload or {}
    analysis = st.session_state.last_analysis or {}

    raw = [
        (payload.get("highlights") or {}).get("overlay_path"),
        (analysis.get("artifacts_v1") or {}).get("overlay_path") if isinstance(analysis, dict) else None,
        analysis.get("overlay_path") if isinstance(analysis, dict) else None,
    ]
    return [Path(str(c)) for c in raw if c]


def _resolve_overlay_path() -> Path | None:
    for p in _overlay_debug_candidates():
        try:
            if p.exists() and p.stat().st_size > 0:
                return p
        except Exception:
            continue
    return None


def _compute_lift_quality(analysis: dict[str, Any] | None) -> int | None:
    if not isinstance(analysis, dict):
        return None
    reps = analysis.get("reps") if isinstance(analysis.get("reps"), list) else []
    if not reps:
        return None

    rep_scores = []
    for rep in reps:
        r = rep if isinstance(rep, dict) else {}
        score = 100
        level = str((r.get("confidence_v1") or {}).get("level") or "").lower()
        if level == "low":
            score -= 10
        faults = r.get("faults_v1") if isinstance(r.get("faults_v1"), list) else []
        for _ in faults:
            score -= 8
        rom = r.get("rom")
        if isinstance(rom, (int, float)) and rom < 0.75:
            score -= 10
        rep_scores.append(max(0, min(100, score)))

    return int(round(sum(rep_scores) / len(rep_scores))) if rep_scores else None


def _quality_color(score: int | None) -> tuple[str, str]:
    if score is None:
        return "#8a8f98", "n/a"
    if score >= 80:
        return "#35d07f", "Green"
    if score >= 50:
        return "#f0c04f", "Yellow"
    return "#f25f5c", "Red"


def _run_pipeline(upload, exercise: str, user_message: str, load_kg: float | None):
    tmp_path = _safe_tmp_video(upload)

    prog = st.progress(0, text="Tracking pose…")
    analyzer = RepRightAnalyzer()
    analysis = analyzer.analyze(str(tmp_path), exercise)

    prog.progress(60, text="Building coach context…")
    payload = build_coach_payload(
        analysis,
        message=user_message,
        load_kg=load_kg,
        history=st.session_state.history[-6:],
    )

    prog.progress(85, text="Generating coaching response…")
    response = run_coach(payload)

    prog.progress(100, text="Done.")
    time.sleep(0.1)
    prog.empty()

    return analysis, payload, response


def _new_chat(exercise: str) -> None:
    thread_id = _new_thread_id(exercise)
    st.session_state.thread_id = thread_id
    st.session_state.thread_created_at = _now_iso()
    st.session_state.thread_title = _thread_title(st.session_state.thread_created_at, exercise)
    st.session_state.history = []
    st.session_state.last_analysis = None
    st.session_state.last_payload = None
    st.session_state.last_response = None
    st.session_state.active_upload_sig = None
    st.session_state.pending_upload_sig = None
    st.session_state.pending_upload_name = None
    _save_thread(thread_id)


st.set_page_config(page_title="RepRight", layout="wide", initial_sidebar_state="expanded")
_inject_css()

for key in ["thread_id", "thread_created_at", "thread_title", "history", "last_analysis", "last_payload", "last_response", "active_upload_sig", "pending_upload_sig", "pending_upload_name"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "history" else None

if st.session_state.thread_id is None:
    _new_chat("bench")

with st.sidebar:
    if st.button("+ New chat", use_container_width=True):
        _new_chat(st.session_state.get("exercise_choice") or "bench")
        st.rerun()

    q = st.text_input("Search chats", value="")
    st.markdown("### Chats")

    thread_items = list_threads()
    if q.strip():
        needle = q.strip().lower()
        thread_items = [t for t in thread_items if needle in str(t.get("title") or t.get("thread_id") or "").lower()]

    for thread in thread_items:
        tid = thread.get("thread_id")
        if not tid:
            continue
        title = thread.get("title") or tid
        subtitle = ""
        analysis_json = ((thread.get("analysis_ref") or {}).get("analysis_json"))
        if analysis_json:
            try:
                ap = Path(str(analysis_json))
                if ap.exists():
                    data = json.loads(ap.read_text(encoding="utf-8"))
                    n_reps = (data.get("set_summary_v1") or {}).get("n_reps")
                    if isinstance(n_reps, int):
                        subtitle = f"n_reps={n_reps}"
            except Exception:
                subtitle = ""

        if st.button(f"{title}{' — ' + subtitle if subtitle else ''}", key=f"thread_{tid}", use_container_width=True):
            _load_thread(tid)
            st.rerun()

status_ready = "Analyzing" if st.session_state.get("_analyzing") else "Ready"
pill_class = "rr-busy" if status_ready == "Analyzing" else "rr-ready"

st.markdown(
    f"""
    <div class='rr-header'>
      <div class='rr-title'>🏋️ RepRight</div>
      <div class='rr-sub'>Video-based rep analysis and coaching chat.</div>
      <span class='rr-pill {pill_class}'>{status_ready}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.05, 0.95], gap="large")

with left:
    exercise = st.selectbox("Exercise", EXERCISES, key="exercise_choice")
    load_kg = st.number_input("Load (kg)", min_value=0.0, value=0.0)
    use_load = load_kg if load_kg > 0 else None

    upload = st.file_uploader("Upload set video", type=["mp4", "mov", "m4v", "avi", "mkv", "webm"])
    user_message = st.text_input("Optional note to coach", value="")

    upload_ready = upload is not None
    if upload is not None:
        upload_sig = _upload_signature(upload)
        active_sig = st.session_state.get("active_upload_sig")
        pending_sig = st.session_state.get("pending_upload_sig")

        if active_sig and upload_sig != active_sig and pending_sig != upload_sig:
            st.session_state.pending_upload_sig = upload_sig
            st.session_state.pending_upload_name = upload.name
            upload_ready = False

        if st.session_state.get("pending_upload_sig") == upload_sig:
            st.warning("⚠️ Uploading a new video will start a new chat and keep the previous chat saved. Press OK to continue.")
            ok_col, cancel_col = st.columns(2)
            with ok_col:
                if st.button("OK - Start new chat", use_container_width=True):
                    _new_chat(exercise)
                    st.session_state.active_upload_sig = upload_sig
                    st.session_state.pending_upload_sig = None
                    st.session_state.pending_upload_name = None
                    st.info("Started a new blank chat for this upload.")
                    st.rerun()
            with cancel_col:
                if st.button("Cancel upload switch", use_container_width=True):
                    st.session_state.pending_upload_sig = None
                    st.session_state.pending_upload_name = None
                    upload_ready = False
            upload_ready = False
        elif active_sig is None:
            st.session_state.active_upload_sig = upload_sig

    if st.button("Analyze set", use_container_width=True):
        if upload is None:
            st.warning("Upload a video first.")
        elif not upload_ready:
            st.warning("Confirm starting a new chat for this upload before analyzing.")
        else:
            try:
                st.session_state._analyzing = True
                analysis, payload, response = _run_pipeline(upload, exercise, user_message, use_load)
                st.session_state.last_analysis = analysis
                st.session_state.last_payload = payload
                st.session_state.last_response = response
                st.session_state.active_upload_sig = _upload_signature(upload)

                if st.session_state.thread_id is None:
                    _new_chat(exercise)

                if user_message.strip():
                    _append_history("user", user_message.strip())
                _append_history("assistant", response.get("response_text", ""))
                _save_thread(st.session_state.thread_id)
            except Exception as e:
                st.error("Analysis failed.")
                st.exception(e)
            finally:
                st.session_state._analyzing = False

    overlay_path = _resolve_overlay_path()
    if overlay_path is not None:
        st.markdown('<div class="rr-card">', unsafe_allow_html=True)
        st.caption("Overlay")
        try:
            st.video(overlay_path.read_bytes())
        except Exception:
            st.video(str(overlay_path))
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.last_analysis:
        ss = (st.session_state.last_analysis.get("set_summary_v1") or {}) if isinstance(st.session_state.last_analysis, dict) else {}
        st.markdown('<div class="rr-card">', unsafe_allow_html=True)
        st.caption("Set summary")
        st.json(
            {
                "n_reps": ss.get("n_reps"),
                "avg_rom": ss.get("avg_rom"),
                "avg_duration_sec": ss.get("avg_duration_sec"),
                "avg_tempo_up_sec": ss.get("avg_tempo_up_sec"),
                "avg_tempo_down_sec": ss.get("avg_tempo_down_sec"),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

with right:
    score = _compute_lift_quality(st.session_state.last_analysis)
    color, zone = _quality_color(score)
    st.markdown(
        f"""
        <div class='rr-card'>
          <div style='font-size:0.9rem;opacity:0.85;'>Lift quality</div>
          <div style='display:flex;align-items:center;gap:10px;'>
            <span style='width:14px;height:14px;border-radius:50%;display:inline-block;background:{color};'></span>
            <span style='font-weight:800;font-size:1.2rem;'>{score if score is not None else 'n/a'}%</span>
            <span style='opacity:0.8;font-size:0.85rem;'>{zone}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for msg in st.session_state.history:
        role = "user" if msg.get("role") == "user" else "assistant"
        st.chat_message(role).write(msg.get("content", ""))

    follow = st.chat_input("Ask a follow-up…")
    if follow and st.session_state.last_analysis:
        payload = build_coach_payload(
            st.session_state.last_analysis,
            message=follow,
            load_kg=use_load,
            history=st.session_state.history[-8:],
        )
        response = run_coach(payload)
        st.session_state.last_payload = payload
        st.session_state.last_response = response

        _append_history("user", follow)
        _append_history("assistant", response.get("response_text", ""))
        _save_thread(st.session_state.thread_id)
        st.rerun()

    if st.session_state.last_payload:
        with st.expander("Debug payload"):
            st.json(st.session_state.last_payload)
