import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List

import streamlit as st

# Make sure we can import scripts.engine when running via `streamlit run`
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scripts.engine import analyze_video  # type: ignore[attr-defined]

EXERCISES = ["bench", "curl", "squat", "deadlift"]

RAW_DIR = BASE_DIR / "data" / "raw"
OVERLAY_DIR = BASE_DIR / "data" / "processed" / "overlays"


def _list_dataset_videos() -> Dict[str, List[Path]]:
    """
    Find all .mp4 clips under data/raw/{exercise}/ for our four lifts.
    Returns: { "bench": [Path(...), ...], ... }
    """
    videos: Dict[str, List[Path]] = {}
    for ex in EXERCISES:
        folder = RAW_DIR / ex
        if folder.exists():
            clips = sorted(folder.glob("*.mp4"))
            if clips:
                videos[ex] = clips
    return videos


def _angle_summary(exercise: str, angle_rom: Optional[Dict[str, float]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Turn avg_angle_rom (e.g. {"elbow": 56.7}) into a short verdict and explanation.
    Returns (label, explanation) or (None, None) if we can't say anything.
    """
    if not angle_rom:
        return None, None

    # Take first joint entry
    joint, value = next(iter(angle_rom.items()))
    joint_name = joint.capitalize()

    label: str
    explanation: str

    # Simple, literature-inspired heuristics – good enough for a prototype
    if exercise == "bench":
        # elbow ROM: want something like ~40–70°+ for visible pressing
        if value < 20:
            label = "Very shallow press"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Bar path is very short – likely not reaching the chest."
        elif value < 40:
            label = "Shallow/moderate press"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Some motion, but could benefit from a deeper press."
        else:
            label = "Good press depth"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. This suggests a reasonably full pressing range."

    elif exercise == "curl":
        # elbow ROM: want big flexion (~60°+) for full contraction
        if value < 30:
            label = "Minimal curl ROM"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. The elbow barely moves – likely just swinging."
        elif value < 60:
            label = "Partial curl"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Decent motion, but not a full curl."
        else:
            label = "Good curl ROM"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. This looks like a strong elbow flexion range."

    elif exercise == "squat":
        # knee ROM: depth proxy – higher is deeper
        if value < 20:
            label = "Very shallow squat"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Likely just a slight bend, far from parallel."
        elif value < 40:
            label = "Shallow squat"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Quarter/half-depth – room to sit deeper."
        else:
            label = "Good squat depth"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Indicates a solid depth pattern."

    elif exercise == "deadlift":
        # hip ROM: hinge quality – larger means more hip travel
        if value < 10:
            label = "Minimal hip hinge"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Very small hip motion – bar may be barely moving."
        elif value < 25:
            label = "Partial hip hinge"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Some hip motion, but hinge could be stronger."
        else:
            label = "Good hip hinge"
            explanation = f"{joint_name} ROM ≈ {value:.1f}°. Suggests a meaningful deadlift-style hip hinge."

    else:
        label = f"{joint_name} ROM ≈ {value:.1f}°"
        explanation = None

    return label, explanation


def _find_overlay(exercise: str, video_path: str) -> Optional[Path]:
    """
    Given e.g. exercise='bench' and video_path='data/raw/bench/bench press_37.mp4',
    try both the new overlay layout and the legacy one.
    """
    try:
        stem = Path(video_path).stem  # e.g. "bench press_37"
    except Exception:
        return None

    candidates = [
        OVERLAY_DIR / exercise / f"{stem}_overlay.mp4",           # new layout
        PROCESSED_ROOT / exercise / f"{stem}_overlay.mp4",        # legacy layout
    ]

    for p in candidates:
        if p.exists():
            return p

    return None


def main() -> None:
    st.set_page_config(page_title="RepRight Prototype", layout="wide")
    st.title("RepRight – Prototype Exercise Coach")

    st.markdown(
        """
Prototype Streamlit interface for your thesis system.

1. Choose an exercise and a recorded clip from the dataset.  
2. Run analysis to see rep metrics, difficulty, and joint-angle ROM.  
3. (If available) view the skeleton overlay video.
"""
    )

    videos_by_ex = _list_dataset_videos()
    if not videos_by_ex:
        st.error("No dataset videos found under `data/raw/*`. Make sure your dataset is in place.")
        return

    # --- Sidebar controls ---
    with st.sidebar:
        st.header("Select Clip")

        valid_exercises = [ex for ex in EXERCISES if ex in videos_by_ex and videos_by_ex[ex]]
        if not valid_exercises:
            st.error("No videos discovered for any exercise under `data/raw`.")
            return

        exercise = st.selectbox("Exercise", options=valid_exercises, index=0)

        clips = videos_by_ex.get(exercise, [])
        clip = st.selectbox(
            "Clip",
            options=clips,
            index=0,
            format_func=lambda p: p.name,
        )

        run_button = st.button("Analyze Clip", type="primary")

    if not run_button:
        st.info("Pick an exercise and clip in the sidebar, then click **Analyze Clip**.")
        return

    # --- Run analysis ---
    video_path_str = str(clip)
    try:
        result: Dict[str, Any] = analyze_video(video_path_str, exercise)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        return

    # --- Layout: left = summary, right = overlay / extra ---
    col_left, col_right = st.columns([2, 2])

    with col_left:
        st.subheader("Summary")

        st.write(f"**Exercise:** `{result.get('exercise', exercise)}`")
        st.write(f"**Video:** `{result.get('video', video_path_str)}`")
        st.write(f"**Valid:** {result.get('valid', True)}")
        st.write(f"**Difficulty:** {result.get('difficulty', 'unknown')}")

        n_reps = result.get("n_reps") or result.get("reps")
        if n_reps is not None:
            st.write(f"**Reps detected:** {int(n_reps)}")

        avg_rom = result.get("avg_rom")
        if avg_rom is not None:
            st.write(f"**Avg normalized ROM:** {avg_rom:.3f}")

        avg_dur = result.get("avg_duration_sec") or result.get("avg_duration")
        if avg_dur is not None:
            st.write(f"**Avg rep duration:** {avg_dur:.2f} s")

        angle_rom = result.get("avg_angle_rom") or result.get("avg_joint_rom")
        if angle_rom:
            # show the raw angle
            joint, value = next(iter(angle_rom.items()))
            st.write(f"**Avg {joint} ROM:** {value:.1f}°")

            label, explanation = _angle_summary(exercise, angle_rom)
            if label:
                st.markdown(f"**Angle verdict:** {label}")
            if explanation:
                st.caption(explanation)

        overall = result.get("overall") or result.get("summary")
        if overall:
            st.markdown(f"**Overall note:** {overall}")

        load_suggestion = result.get("load_suggestion")
        rep_range_suggestion = result.get("rep_range_suggestion")

        if load_suggestion or rep_range_suggestion:
            st.subheader("Training Suggestions")
        if load_suggestion:
            st.write(f"- **Load:** {load_suggestion}")
        if rep_range_suggestion:
            st.write(f"- **Rep range:** {rep_range_suggestion}")

        # Per-rep feedback (compact)
        per_rep = result.get("per_rep_feedback") or result.get("per_rep")
        if per_rep:
            st.subheader("Per-Rep Feedback")
            for rep in per_rep:
                idx = rep.get("rep_index") or rep.get("metrics", {}).get("rep_index")
                msg = rep.get("analysis", {}).get("message", "")
                rom_val = rep.get("metrics", {}).get("rom")
                dur_val = rep.get("metrics", {}).get("duration_sec")

                bullet = f"**Rep {idx}:** {msg}"
                details: list[str] = []
                if rom_val is not None:
                    details.append(f"ROM={rom_val:.3f}")
                if dur_val is not None:
                    details.append(f"dur={dur_val:.2f}s")
                if details:
                    bullet += f" _( {' · '.join(details)} )_"

                st.markdown(f"- {bullet}")

    with col_right:
        st.subheader("Pose Overlay (if available)")

        overlay_path = _find_overlay(exercise, result.get("video", video_path_str))
        if overlay_path is not None:
            st.video(str(overlay_path))
        else:
            st.info(
                "No overlay video found for this clip yet.\n\n"
                "Expected location:\n"
                f"`{OVERLAY_DIR / exercise / (Path(video_path_str).stem + '_overlay.mp4')}`"
            )

        st.markdown("---")
        st.caption(
            "This prototype uses precomputed metrics (including normalized ROM and joint-angle ROM) "
            "to provide basic rep counting, difficulty estimation, and technique feedback."
        )


if __name__ == "__main__":
    main()
