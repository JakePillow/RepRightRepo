from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


EXPECTED_COLS = {
    "exercise": ["exercise"],
    "expected": ["expected_reps", "true_reps", "gt_reps", "actual_reps"],
    "predicted": ["pred_reps", "predicted_reps", "reps_pred", "predicted"],
    "video": ["video", "video_id", "filename", "clip", "name"],
    "abs_error": ["abs_error", "rep_error_abs", "absolute_error"],
}


def resolve_col(df: pd.DataFrame, logical_name: str) -> str:
    for candidate in EXPECTED_COLS[logical_name]:
        if candidate in df.columns:
            return candidate
    raise KeyError(f"Could not resolve required column '{logical_name}' from {list(df.columns)}")


def load_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        return {}
    with summary_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_per_exercise(df: pd.DataFrame) -> pd.DataFrame:
    ex_col = resolve_col(df, "exercise")
    true_col = resolve_col(df, "expected")
    pred_col = resolve_col(df, "predicted")
    frame = df[[ex_col, true_col, pred_col]].copy()
    frame["ae"] = (frame[pred_col] - frame[true_col]).abs()
    out = frame.groupby(ex_col).apply(
        lambda g: pd.Series(
            {
                "n": len(g),
                "mae": g["ae"].mean(),
                "exact_pct": (g["ae"] == 0).mean() * 100.0,
                "pm1_pct": (g["ae"] <= 1).mean() * 100.0,
            }
        )
    )
    out = out.reset_index().rename(columns={ex_col: "exercise"})
    return out


def save_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def plot_performance_by_exercise(per_ex: pd.DataFrame, outpath: Path) -> None:
    labels = per_ex["exercise"].tolist()
    x = np.arange(len(labels))
    width = 0.25
    plt.figure(figsize=(9, 5))
    plt.bar(x - width, per_ex["mae"], width=width, label="MAE")
    plt.bar(x, per_ex["exact_pct"], width=width, label="Exact %")
    plt.bar(x + width, per_ex["pm1_pct"], width=width, label="±1 %")
    plt.xticks(x, labels)
    plt.ylabel("Value")
    plt.xlabel("Exercise")
    plt.title("Figure 4.1 Performance by Exercise")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_predicted_vs_expected(df: pd.DataFrame, outpath: Path) -> None:
    true_col = resolve_col(df, "expected")
    pred_col = resolve_col(df, "predicted")
    lo = min(df[true_col].min(), df[pred_col].min())
    hi = max(df[true_col].max(), df[pred_col].max())
    plt.figure(figsize=(6, 6))
    plt.scatter(df[true_col], df[pred_col])
    plt.plot([lo, hi], [lo, hi])
    plt.xlabel("Expected reps")
    plt.ylabel("Predicted reps")
    plt.title("Figure 4.2 Predicted vs Expected")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def plot_abs_error_per_video(df: pd.DataFrame, outpath: Path) -> None:
    video_col = resolve_col(df, "video")
    if "abs_error" in df.columns:
        err_col = "abs_error"
    else:
        true_col = resolve_col(df, "expected")
        pred_col = resolve_col(df, "predicted")
        df = df.copy()
        df["abs_error"] = (df[pred_col] - df[true_col]).abs()
        err_col = "abs_error"
    sdf = df[[video_col, err_col]].sort_values(err_col, ascending=False)
    plt.figure(figsize=(10, 5))
    plt.bar(sdf[video_col], sdf[err_col])
    plt.xticks(rotation=70, ha="right")
    plt.ylabel("Absolute error")
    plt.xlabel("Video")
    plt.title("Figure 4.3 Absolute Error per Video")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def write_placeholder_note(name: str, outdir: Path, message: str) -> None:
    p = outdir / f"{name}_PLACEHOLDER.txt"
    p.write_text(message, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    results_path = Path(args.results)
    summary_path = Path(args.summary)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not results_path.exists():
        raise FileNotFoundError(results_path)

    df = pd.read_csv(results_path)
    summary = load_summary(summary_path)

    if "abs_error" not in df.columns:
        tcol = resolve_col(df, "expected")
        pcol = resolve_col(df, "predicted")
        df["abs_error"] = (df[pcol] - df[tcol]).abs()

    per_ex = compute_per_exercise(df)
    pred_pairs = df[[resolve_col(df, "video"), resolve_col(df, "exercise"), resolve_col(df, "expected"), resolve_col(df, "predicted"), "abs_error"]].copy()
    pred_pairs.columns = ["video", "exercise", "expected_reps", "predicted_reps", "abs_error"]

    save_table(per_ex, outdir / "table_4_2_per_exercise.csv")
    save_table(pred_pairs, outdir / "table_4_3_per_video.csv")
    save_table(pred_pairs[["video", "exercise", "expected_reps", "predicted_reps"]], outdir / "predicted_vs_expected_pairs.csv")

    plot_performance_by_exercise(per_ex, outdir / "figure_4_1_performance_by_exercise.png")
    plot_predicted_vs_expected(df, outdir / "figure_4_2_predicted_vs_expected.png")
    plot_abs_error_per_video(df, outdir / "figure_4_3_abs_error_per_video.png")

    write_placeholder_note(
        "figure_4_4",
        outdir,
        "Generate from per-rep trajectory artifacts after final run: plot normalized knee/hip angle for squat and elbow angle for curl using one correct and one faulty exemplar.",
    )
    write_placeholder_note(
        "figure_4_5",
        outdir,
        "Generate from deadlift/selected exercise driver-signal artifacts after final run: plot driver signal vs time, state labels, and rep boundaries.",
    )
    write_placeholder_note(
        "figure_4_6",
        outdir,
        "Generate from overlay videos after final run: extract 3-5 representative annotated frames per clip showing skeleton, boundary, and fault label.",
    )
    write_placeholder_note(
        "figure_4_7",
        outdir,
        "Generate from intended_fault vs predicted_fault columns if available, or from evaluation labels joined to analysis faults. Counts only, no accuracy claim.",
    )

    manifest = {
        "results_csv": str(results_path),
        "summary_json": str(summary_path),
        "rows": int(len(df)),
        "figures_generated": [
            "figure_4_1_performance_by_exercise.png",
            "figure_4_2_predicted_vs_expected.png",
            "figure_4_3_abs_error_per_video.png",
        ],
        "tables_generated": [
            "table_4_2_per_exercise.csv",
            "table_4_3_per_video.csv",
            "predicted_vs_expected_pairs.csv",
        ],
        "summary_present": bool(summary),
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
