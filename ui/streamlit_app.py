from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys
import time
import json
from datetime import datetime

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach

EXERCISES = ["bench", "deadlift", "squat", "curl"]

# =============================
# Persistent Chat Storage
# =============================

CHATS_DIR = ROOT / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)


def _new_thread_id(exercise: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{exercise}"


def _thread_path(thread_id: str) -> Path:
    return CHATS_DIR / f"{thread_id}.json"


def _save_thread(thread_id: str) -> None:
    analysis = st.session_state.last_analysis or {}

    thread = {
        "thread_id": thread_id,
        "created_at": st.session_state.get("thread_created_at"),
        "updated_at": datetime.now().isoformat(),
        "exercise": analysis.get("exercise"),
        "analysis_ref": {
            "analysis_json": analysis.get("metrics_path"),
            "overlay_path": analysis.get("overlay_path"),
        },
        "history": st.session_state.history,
    }

    _thread_path(thread_id).write_text(json.dumps(thread, indent=2), encoding="utf-8")


def _load_thread(thread_id: str) -> None:
    p = _thread_path(thread_id)
    if not p.exists():
        return

    thread = json.loads(p.read_text(encoding="utf-8"))

    st.session_state.thread_id = thread["thread_id"]
    st.session_state.thread_created_at = thread.get("created_at")
    st.session_state.history = thread.get("history", [])
    st.session_state.last_analysis = {
        "exercise": thread.get("exercise"),
        "overlay_path": (thread.get("analysis_ref") or {}).get("overlay_path"),
        "metrics_path": (thread.get("analysis_ref") or {}).get("analysis_json"),
    }


# =============================
# UI Helpers
# =============================

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Nunito', system-ui, sans-serif; }

        .stApp {
          background: radial-gradient(1200px 800px at 10% 10%, rgba(255,255,255,0.08), rgba(0,0,0,0.0)),
                      linear-gradient(180deg, rgba(20,24,34,1) 0%, rgba(10,12,18,1) 100%);
        }

        .rr-card {
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          border-radius: 18px;
          padding: 14px 16px;
          margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _safe_tmp_video(upload) -> Path:
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)
    p = Path(path)
    p.write_bytes(upload.getbuffer())
    return p


# =============================
# Overlay Reliability
# =============================

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


def _try_show_overlay_bytes() -> None:
    overlay_file = _resolve_overlay_path()
    if overlay_file is None:
        return

    st.markdown('<div class="rr-card">', unsafe_allow_html=True)
    st.caption("Overlay")

    try:
        st.video(overlay_file.read_bytes())
    except Exception:
        st.video(str(overlay_file))

    st.markdown("</div>", unsafe_allow_html=True)


# =============================
# Pipeline Runner
# =============================

def _run_pipeline(upload, exercise: str, user_message: str, load_kg: float | None):
    tmp_path = _safe_tmp_video(upload)

    anim_slot = st.empty()
    anim_path = ROOT / "ui" / "assets" / "loading_lift.mp4"
    if anim_path.exists():
        anim_slot.video(str(anim_path), loop=True, autoplay=True)

    prog = st.progress(0, text="Tracking pose…")
    time.sleep(0.05)

    analyzer = RepRightAnalyzer()
    analysis = analyzer.analyze(str(tmp_path), exercise)

    prog.progress(60, text="Building coach context…")
    payload = build_coach_payload(analysis, message=user_message, load_kg=load_kg)

    prog.progress(85, text="Generating coaching response…")
    response = run_coach(payload)

    prog.progress(100, text="Done.")
    time.sleep(0.1)

    prog.empty()
    anim_slot.empty()

    return analysis, payload, response


# =============================
# App Start
# =============================

st.set_page_config(page_title="RepRight", layout="wide")
_inject_css()

# Session State Init
for key in ["history", "last_analysis", "last_payload", "last_response", "thread_id", "thread_created_at"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "history" else []

# =============================
# Sidebar
# =============================

with st.sidebar:
    exercise = st.selectbox("Exercise", EXERCISES)
    load_kg = st.number_input("Load (kg)", min_value=0.0, value=0.0)
    use_load = load_kg if load_kg > 0 else None

    if st.button("New chat"):
        st.session_state.history = []
        st.session_state.last_analysis = None
        st.session_state.last_payload = None
        st.session_state.last_response = None
        st.session_state.thread_id = None
        st.session_state.thread_created_at = None
        st.rerun()

    st.divider()
    st.markdown("### Saved Chats")

    threads = sorted(CHATS_DIR.glob("*.json"), reverse=True)
    options = ["<none>"] + [t.stem for t in threads]

    selected = st.selectbox("Resume chat", options)
    if selected != "<none>" and st.button("Load chat"):
        _load_thread(selected)
        st.rerun()

# =============================
# Main Layout
# =============================

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    upload = st.file_uploader("Upload set video", type=["mp4", "mov", "m4v", "avi", "mkv", "webm"])
    user_message = st.text_input("Optional note to coach", value="")

    if st.button("Analyze set"):
        if upload is None and not st.session_state.last_analysis:
            st.warning("Upload a video first.")
        else:
            try:
                if upload is not None:
                    analysis, payload, response = _run_pipeline(upload, exercise, user_message, use_load)
                    st.session_state.last_analysis = analysis
                    st.session_state.last_payload = payload
                    st.session_state.last_response = response
                else:
                    analysis = st.session_state.last_analysis
                    payload = build_coach_payload(analysis, message=user_message, load_kg=use_load)
                    response = run_coach(payload)
                    st.session_state.last_payload = payload
                    st.session_state.last_response = response

                if st.session_state.thread_id is None:
                    st.session_state.thread_id = _new_thread_id(exercise)
                    st.session_state.thread_created_at = datetime.now().isoformat()

                if user_message.strip():
                    st.session_state.history.append({"role": "user", "content": user_message.strip()})
                st.session_state.history.append({"role": "assistant", "content": response["response_text"]})

                _save_thread(st.session_state.thread_id)

            except Exception as e:
                st.error("Analysis failed.")
                st.exception(e)

    if st.session_state.last_analysis:
        _try_show_overlay_bytes()

with right:
    for msg in st.session_state.history:
        st.chat_message("user" if msg["role"] == "user" else "assistant").write(msg["content"])

    follow = st.chat_input("Ask a follow-up…")
    if follow and st.session_state.last_payload:
        follow_payload = dict(st.session_state.last_payload)
        follow_payload["user_message"] = follow
        follow_payload["history"] = st.session_state.history

        response = run_coach(follow_payload)

        st.session_state.history.append({"role": "user", "content": follow})
        st.session_state.history.append({"role": "assistant", "content": response["response_text"]})
        st.session_state.last_response = response

        if st.session_state.thread_id:
            _save_thread(st.session_state.thread_id)

        st.rerun()

    if st.session_state.last_payload:
        with st.expander("Debug"):
            st.json(st.session_state.last_payload)
            for idx, cand in enumerate(_overlay_debug_candidates(), start=1):
                try:
                    exists = cand.exists()
                    size = cand.stat().st_size if exists else 0
                except Exception:
                    exists, size = False, 0
                st.caption(f"{cand} | exists={exists} | bytes={size}")