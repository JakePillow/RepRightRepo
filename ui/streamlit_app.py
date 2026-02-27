from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path
import sys
import time

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach

EXERCISES = ["bench", "deadlift", "squat", "curl"]


# ----------------------------
# UI helpers
# ----------------------------

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* --- Wii-ish soft UI vibe --- */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap');

        html, body, [class*="css"]  { font-family: 'Nunito', system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }

        /* Page background */
        .stApp {
          background: radial-gradient(1200px 800px at 10% 10%, rgba(255,255,255,0.08), rgba(0,0,0,0.0)),
                      linear-gradient(180deg, rgba(20,24,34,1) 0%, rgba(10,12,18,1) 100%);
        }

        /* Card containers */
        .rr-card {
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          border-radius: 18px;
          padding: 14px 16px;
          box-shadow: 0 8px 20px rgba(0,0,0,0.25);
          margin-bottom: 12px;
        }

        /* Headline */
        .rr-title {
          font-size: 34px;
          font-weight: 800;
          letter-spacing: 0.2px;
          margin: 0 0 4px 0;
        }
        .rr-subtitle {
          opacity: 0.85;
          margin: 0 0 8px 0;
        }

        /* Buttons */
        div.stButton > button {
          border-radius: 14px;
          padding: 0.6rem 1rem;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.06);
        }
        div.stButton > button:hover {
          border: 1px solid rgba(255,255,255,0.20);
          background: rgba(255,255,255,0.10);
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
          background: rgba(255,255,255,0.03);
          border-right: 1px solid rgba(255,255,255,0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <div class="rr-card">
          <div class="rr-title">RepRight</div>
          <div class="rr-subtitle">Vision-based rep analysis + coaching (chat)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _safe_tmp_video(upload) -> Path:
    # Avoid collisions: use a unique temp file
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)
    p = Path(path)
    p.write_bytes(upload.getbuffer())
    return p


def _file_exists(p: str | None) -> bool:
    if not p:
        return False
    try:
        return Path(p).exists()
    except Exception:
        return False


def _try_show_overlay(analysis: dict) -> None:
    # analysis may contain overlay in top-level or artifacts_v1
    overlay = analysis.get("overlay_path") or (analysis.get("artifacts_v1") or {}).get("overlay_path")
    if overlay and _file_exists(overlay):
        st.markdown('<div class="rr-card">', unsafe_allow_html=True)
        st.caption("Overlay (if available)")
        st.video(str(overlay))
        st.markdown("</div>", unsafe_allow_html=True)


def _rep_table_rows(analysis: dict) -> list[dict]:
    reps = analysis.get("reps") or []
    rows = []
    for r in reps:
        faults = r.get("faults_v1") or []
        rows.append(
            {
                "rep": r.get("rep_index"),
                "rom": r.get("rom"),
                "dur_s": r.get("duration_sec"),
                "down_s": r.get("tempo_down_sec"),
                "up_s": r.get("tempo_up_sec"),
                "conf": (r.get("confidence_v1") or {}).get("level"),
                "faults": ", ".join([f.get("code", "") for f in faults]) if faults else "",
            }
        )
    return rows


def _show_analysis_summary(analysis: dict) -> None:
    st.markdown('<div class="rr-card">', unsafe_allow_html=True)
    ss = analysis.get("set_summary_v1") or {}
    cols = st.columns(4)
    cols[0].metric("Exercise", analysis.get("exercise", "?"))
    cols[1].metric("Reps", ss.get("n_reps", 0))
    cols[2].metric("Avg ROM", f"{ss.get('avg_rom', 0.0):.3f}")
    cols[3].metric("Avg Duration (s)", f"{ss.get('avg_duration_sec', 0.0):.3f}")
    st.markdown("</div>", unsafe_allow_html=True)

    rows = _rep_table_rows(analysis)
    st.markdown('<div class="rr-card">', unsafe_allow_html=True)
    st.caption("Per-rep summary")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No reps detected for this set (analysis still saved).")
    st.markdown("</div>", unsafe_allow_html=True)


def _run_pipeline(upload, exercise: str, user_message: str, load_kg: float | None) -> tuple[dict, dict]:
    tmp_path = _safe_tmp_video(upload)

    # Loading animation (clears when done)
    anim_slot = st.empty()
    anim_path = ROOT / "ui" / "assets" / "loading_lift.mp4"
    if anim_path.exists():
        anim_slot.video(str(anim_path), loop=True, autoplay=True)

    prog = st.progress(0, text="Tracking pose…")
    time.sleep(0.05)
    prog.progress(15, text="Tracking pose…")

    analyzer = RepRightAnalyzer()
    analysis = analyzer.run(tmp_path, exercise)

    prog.progress(60, text="Building coach context…")
    payload = build_coach_payload(analysis, message=user_message, load_kg=load_kg)

    prog.progress(85, text="Generating coaching response…")
    response = run_coach(payload)

    prog.progress(100, text="Done.")
    time.sleep(0.1)

    # Clear UI elements
    prog.empty()
    anim_slot.empty()

    return payload, response


# ----------------------------
# App
# ----------------------------

_inject_css()
st.set_page_config(page_title="RepRight", layout="wide")
_render_header()

if "history" not in st.session_state:
    st.session_state.history = []  # list[{role, content}]
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None


with st.sidebar:
    st.markdown("### Session")
    exercise = st.selectbox("Exercise", EXERCISES, index=0)
    load_kg = st.number_input("Load (kg)", min_value=0.0, value=0.0, step=2.5)
    use_load = (load_kg if load_kg > 0 else None)

    st.divider()
    st.markdown("### Controls")
    if st.button("New chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_analysis = None
        st.session_state.last_payload = None
        st.session_state.last_response = None
        st.rerun()

    if st.session_state.last_analysis:
        ss = st.session_state.last_analysis.get("set_summary_v1") or {}
        st.caption("Last analysis")
        st.write(
            {
                "exercise": st.session_state.last_analysis.get("exercise"),
                "n_reps": ss.get("n_reps"),
            }
        )


left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown('<div class="rr-card">', unsafe_allow_html=True)
    st.subheader("1) Upload & analyze")
    upload = st.file_uploader("Upload set video", type=["mp4", "mov", "m4v", "avi", "mkv", "webm"])
    st.caption("Tip: Side or 45° camera angle is usually more reliable than front view.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Analyze message (optional)
    user_message = st.text_input("Optional note to coach (e.g., goal / pain / how it felt)", value="")

    if st.button("Analyze set", type="primary", use_container_width=True):
        if upload is None and st.session_state.last_analysis is None:
            st.warning("Upload a video first (or reuse the last analysis in this chat).")
        else:
                try:
                    if upload is not None:
                        payload, response = _run_pipeline(upload, exercise, user_message, use_load)
                        st.session_state.last_payload = payload
                        st.session_state.last_response = response
                        st.session_state.last_analysis = payload.get("analysis_v1") or payload.get("analysis") or st.session_state.last_analysis
                    else:
                        # Reuse last analysis
                        analysis = st.session_state.last_analysis
                        payload = build_coach_payload(analysis, message=user_message, load_kg=use_load)
                        response = run_coach(payload)
                        st.session_state.last_payload = payload
                        st.session_state.last_response = response

                    # Append chat turn
                    if user_message.strip():
                        st.session_state.history.append({"role": "user", "content": user_message.strip()})
                    st.session_state.history.append({"role": "assistant", "content": st.session_state.last_response["response_text"]})

                except Exception as e:
                    st.error("Something went wrong while analyzing this set.")
                    st.exception(e)

    # Show analysis artifacts/summary if available
    if st.session_state.last_analysis:
        _try_show_overlay(st.session_state.last_analysis)
        _show_analysis_summary(st.session_state.last_analysis)

with right:
    st.markdown('<div class="rr-card">', unsafe_allow_html=True)
    st.subheader("2) Chat with your coach")
    st.caption("Follow-ups reuse the last analysis context (no re-upload needed).")
    st.markdown("</div>", unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.history:
        st.chat_message("user" if msg["role"] == "user" else "assistant").write(msg["content"])

    # Chat input for follow-ups
    follow = st.chat_input("Ask a follow-up…")
    if follow and st.session_state.last_payload:
        follow_payload = dict(st.session_state.last_payload)
        follow_payload["user_message"] = follow
        follow_payload["history"] = st.session_state.history

        try:
            response = run_coach(follow_payload)
            st.session_state.last_response = response
            st.session_state.history.append({"role": "user", "content": follow})
            st.session_state.history.append({"role": "assistant", "content": response["response_text"]})
            st.rerun()
        except Exception as e:
            st.error("Coach failed to respond.")
            st.exception(e)

    if st.session_state.last_payload:
        with st.expander("Debug: payload JSON"):
            st.json(st.session_state.last_payload)