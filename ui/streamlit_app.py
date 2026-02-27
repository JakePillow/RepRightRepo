from __future__ import annotations

import tempfile
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach

EXERCISES = ["bench", "deadlift", "squat", "curl"]

st.set_page_config(page_title="RepRight Chat", layout="wide")
st.title("RepRight — Chat Shell")

if "history" not in st.session_state:
    st.session_state.history = []
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None

with st.sidebar:
    exercise = st.selectbox("Exercise", EXERCISES)
    load_kg = st.number_input("Load (kg)", min_value=0.0, value=0.0)
    if st.button("New chat"):
        st.session_state.history = []
        st.session_state.last_analysis = None
        st.session_state.last_payload = None
        st.session_state.last_response = None

upload = st.file_uploader("Upload set video", type=["mp4", "mov", "m4v", "avi", "mkv", "webm"])
user_msg = st.text_input("Message", value="")

if st.button("Run analysis + coach", type="primary"):
    analysis = None

    if upload is not None:
        tmp = Path(tempfile.gettempdir()) / upload.name
        tmp.write_bytes(upload.getbuffer())

        analyzer = RepRightAnalyzer()
        analysis = analyzer.run(tmp, exercise)
        st.session_state.last_analysis = analysis

    elif st.session_state.last_analysis is not None:
        analysis = st.session_state.last_analysis

    else:
        st.warning("Upload a video first, or reuse an existing analysis from this chat.")

    if analysis is not None:
        payload = build_coach_payload(analysis, message=user_msg, load_kg=(load_kg if load_kg > 0 else None))
        response = run_coach(payload)

        st.session_state.last_payload = payload
        st.session_state.last_response = response
        st.session_state.history.append({"user": user_msg, "assistant": response["response_text"]})



def _overlay_debug_candidates() -> list[Path]:
    payload = st.session_state.last_payload or {}
    analysis = st.session_state.last_analysis or {}
    raw = [
        (payload.get("highlights") or {}).get("overlay_path") if isinstance(payload, dict) else None,
        (analysis.get("artifacts_v1") or {}).get("overlay_path") if isinstance(analysis, dict) else None,
        analysis.get("overlay_path") if isinstance(analysis, dict) else None,
    ]
    out: list[Path] = []
    for c in raw:
        if c:
            out.append(Path(str(c)))
    return out


def _resolve_overlay_path() -> Path | None:
    for p in _overlay_debug_candidates():
        if p.exists() and p.stat().st_size > 0:
            return p
    return None

if st.session_state.last_payload:
    st.subheader("Latest coach response")
    st.write(st.session_state.last_response["response_text"])

    st.subheader("Follow-up")
    followup = st.text_input("Ask a follow-up question", key="followup")
    if st.button("Send follow-up") and followup:
        follow_payload = dict(st.session_state.last_payload)
        follow_payload["user_message"] = followup
        follow_payload["history"] = st.session_state.history
        response = run_coach(follow_payload)
        st.session_state.last_response = response
        st.session_state.history.append({"user": followup, "assistant": response["response_text"]})

for turn in st.session_state.history:
    st.chat_message("user").write(turn["user"])
    st.chat_message("assistant").write(turn["assistant"])

overlay_file = _resolve_overlay_path()
if overlay_file is not None:
    st.subheader("Overlay")
    st.video(overlay_file.read_bytes())

if st.session_state.last_payload:
    with st.expander("Payload debug"):
        st.json(st.session_state.last_payload)
        for idx, cand in enumerate(_overlay_debug_candidates(), start=1):
            exists = cand.exists()
            size = cand.stat().st_size if exists else 0
            head = cand.read_bytes()[:12].hex() if exists and size > 0 else ""
            st.caption(f"candidate_{idx} = {cand} | exists={exists} | bytes={size} | head12={head}")
        if not _overlay_debug_candidates():
            st.caption("overlay_path = <none provided>")
