"""
Deprecated prototype evaluation script.
Not used in thesis experiments.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

from repright.analyzer import RepRightAnalyzer
from labels import load_all_labels

REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def parse_rep_good_labels(s: str) -> List[int]:
    s = (s or "").strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",") if p.strip() != ""]
    out: List[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            pass
    return out


def main() -> None:
    rows = load_all_labels()
    analyzer = RepRightAnalyzer()

    out_rows: List[Dict[str, Any]] = []

    for r in rows:
        video_rel = (r.get("video_rel", "") or "").replace("\\", "/").strip()
        if not video_rel:
            continue

        exercise = (r.get("exercise", "") or "").lower().strip()
        if exercise not in {"bench", "curl", "squat", "deadlift"}:
            continue

        expected_reps = int(float(r.get("expected_reps", "0") or 0))
        rep_good = parse_rep_good_labels(r.get("rep_good_labels", ""))

        try:
            res = analyzer.analyze(video_rel, exercise)
            status = "ok"
        except FileNotFoundError:
            res = {}
            status = "missing_metrics"

        pred_reps = int(res.get("n_reps", 0) or 0)

        # Per-rep predicted quality (placeholder for now)
        pred_good: List[int] = []
        reps = res.get("reps") or []
        for _ in reps:
            pred_good.append(1)  # assume good until LLM layer

        n_cmp = min(len(rep_good), len(pred_good))
        rep_acc: Any = ""
        if n_cmp > 0:
            rep_acc = sum(1 for i in range(n_cmp) if rep_good[i] == pred_good[i]) / n_cmp

        out_rows.append({
            "video_rel": video_rel,
            "exercise": exercise,
            "status": status,
            "variant": r.get("variant", ""),
            "camera_angle": r.get("camera_angle", ""),
            "expected_reps": expected_reps,
            "pred_reps": pred_reps,
            "rep_count_ok": int(expected_reps == pred_reps),
            "rep_label_len": len(rep_good),
            "pred_label_len": len(pred_good),
            "rep_label_acc": rep_acc,
            "error_primary_gt": r.get("error_primary", ""),
            "error_secondary_gt": r.get("error_secondary", ""),
        })

    out_path = REPORTS_DIR / "eval_summary.csv"

    fieldnames = list(out_rows[0].keys()) if out_rows else [
        "video_rel", "exercise", "status", "variant", "camera_angle",
        "expected_reps", "pred_reps", "rep_count_ok",
        "rep_label_len", "pred_label_len", "rep_label_acc",
        "error_primary_gt", "error_secondary_gt",
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    print(f"Wrote: {out_path} ({len(out_rows)} rows)")


if __name__ == "__main__":
    main()
