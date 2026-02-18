import os
import json
import time
from pathlib import Path

import streamlit as st

from repright.analyzer import RepRightAnalyzer


# ---------- Constants ----------
REPO_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = REPO_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_EXPECTED = "analysis_v1"  # adjust if you bump schema later


# ---------- Helpers ----------
def _safe_stem(name: str) -> str:
    # keep it simple + filesystem safe
    stem = "".join(c if (c.isalnum() or c in ("-", "_", ".")) else "_" for c in name)
    return stem[:120] if len(stem) > 120 else stem


def save_upload_to_disk(uploaded_file) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = _safe_stem(Path(uploaded_file.name).stem)
    suffix = Path(uploaded_file.name).suffix or ".mp4"
    out_path = UPLOAD_DIR / f"{ts}_{stem}{suffix}"
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return out_path


def fmt_seconds(x):
    try:
        return f"{float(x):.2f}s"
    except Exception:
        return ""


# ---------- Streamlit UI ----------
st.set_page_config(page_title="RepRight", layout="wide")

st.title("RepRight — Video Rep Analysis")

with st.sidebar:
    st.header("Input")
    exercise = st.selectbox("Exercise", ["bench", "squat", "curl", "deadlift"], index=0)
    uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "m4v", "avi"])

    st.divider()
    st.header("Run Controls")
    run_btn = st.button("Analyze", type="primary", disabled=(uploaded is None))

# Keep analyzer instance cached (fast repeated runs)
@st.cache_resource
def get_analyzer():
    return RepRightAnalyzer()

# Store last result in session state
if "last_out" not in st.session_state:
    st.session_state["last_out"] = None
if "last_video_path" not in st.session_state:
    st.session_state["last_video_path"] = None

if run_btn and uploaded is not None:
    video_path = save_upload_to_disk(uploaded)
    st.session_state["last_video_path"] = str(video_path)

    analyzer = get_analyzer()

    with st.spinner("Analyzing video..."):
        out = analyzer.analyze(str(video_path), exercise)

    st.session_state["last_out"] = out

# ---------- Output ----------
out = st.session_state["last_out"]
video_path = st.session_state["last_video_path"]

if out is None:
    st.info("Upload a video and click **Analyze**.")
else:
    # Top summary row
    c1, c2, c3, c4 = st.columns(4)

    schema_version = out.get("schema_version", "")
    ex = out.get("exercise", "")
    n_reps = out.get("n_reps", 0)
    driver = out.get("driver", "")

    c1.metric("Exercise", ex)
    c2.metric("Reps", int(n_reps) if str(n_reps).isdigit() else n_reps)
    c3.metric("Driver", driver)
    c4.metric("Schema", schema_version)

    if schema_version and schema_version != SCHEMA_EXPECTED:
        st.warning(f"Schema mismatch: expected {SCHEMA_EXPECTED} but got {schema_version}")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Video", "Per-rep metrics", "Summary", "Raw JSON"])

    with tab1:
        if video_path and Path(video_path).exists():
            st.video(video_path)
        else:
            st.warning("Uploaded video file not found on disk.")

        # If you have an overlay path in out, show it too
        overlay = out.get("overlay_path") or out.get("overlay_video") or out.get("overlay_rel")
        if overlay:
            ov_path = Path(overlay)
            if not ov_path.is_absolute():
                ov_path = (REPO_ROOT / overlay).resolve()
            if ov_path.exists():
                st.subheader("Overlay")
                st.video(str(ov_path))

    with tab2:
        per_rep = out.get("per_rep") or out.get("reps") or []
        if not per_rep:
            st.info("No per-rep metrics available in output.")
        else:
            # normalize expected keys
            rows = []
            for i, rep in enumerate(per_rep, start=1):
                # Some pipelines use nested analysis dict, some keep rep metrics flat
                analysis = rep.get("analysis") or {}
                rows.append({
                    "rep": rep.get("rep_index", i),
                    "start": rep.get("start_frame", ""),
                    "peak": rep.get("peak_frame", ""),
                    "end": rep.get("end_frame", ""),
                    "rom": rep.get("rom", analysis.get("rom", "")),
                    "duration": fmt_seconds(rep.get("duration_sec", analysis.get("duration_sec", ""))),
                    "tempo_up": fmt_seconds(rep.get("tempo_up_sec", analysis.get("tempo_up_sec", ""))),
                    "tempo_down": fmt_seconds(rep.get("tempo_down_sec", analysis.get("tempo_down_sec", ""))),
                    "quality": analysis.get("quality", rep.get("quality", "")),
                    "notes": ", ".join(analysis.get("notes", [])) if isinstance(analysis.get("notes", []), list) else analysis.get("notes", "")
                })
            st.dataframe(rows, use_container_width=True)

    with tab3:
        summary = out.get("summary") or {}
        if summary:
            st.subheader("Set summary")
            st.json(summary)
        else:
            st.info("No summary object found. Showing common top-level fields instead.")
            st.write({
                "n_reps": out.get("n_reps"),
                "driver": out.get("driver"),
                "fps": out.get("fps"),
                "n_frames": out.get("n_frames"),
            })

        feedback = out.get("feedback") or out.get("flags") or out.get("coaching") or None
        if feedback:
            st.subheader("Feedback")
            st.json(feedback)

    with tab4:
        st.json(out)

    # Download raw JSON
    st.download_button(
        label="Download analysis JSON",
        file_name="analysis.json",
        mime="application/json",
        data=json.dumps(out, indent=2).encode("utf-8"),
        use_container_width=True,
    )
