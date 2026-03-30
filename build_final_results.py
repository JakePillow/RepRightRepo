import csv
import json
from pathlib import Path

gt_path = Path(r"data\eval\ground_truth_custom.csv")
pred_root = Path(r"data\eval_custom")
out_path = Path(r"data\final_results_custom.csv")

rows = list(csv.DictReader(gt_path.open("r", encoding="utf-8-sig")))
out_rows = []

for row in rows:
    video = row["video"]
    exercise = row["exercise"]
    expected_reps = int(row["expected_reps"])
    error_primary = (row.get("error_primary") or "").strip()
    error_secondary = (row.get("error_secondary") or "").strip()

    analysis_path = pred_root / video.replace(".mp4", "") / "analysis_v1.json"

    pred_reps = None
    faults = ""
    overlay_path = ""
    analysis_exists = analysis_path.exists()

    if analysis_exists:
        data = json.loads(analysis_path.read_text(encoding="utf-8"))
        pred_reps = int((data.get("set_summary_v1") or {}).get("n_reps", 0))
        fault_counts = ((data.get("set_summary_v1") or {}).get("fault_counts") or {})
        faults = ";".join(fault_counts.keys())
        overlay_path = data.get("overlay_path") or ""

    rep_error = pred_reps - expected_reps if pred_reps is not None else ""
    abs_error = abs(rep_error) if pred_reps is not None else ""

    out_rows.append({
        "video": video,
        "exercise": exercise,
        "expected_reps": expected_reps,
        "predicted_reps": pred_reps,
        "rep_error": rep_error,
        "abs_error": abs_error,
        "error_primary": error_primary,
        "error_secondary": error_secondary,
        "predicted_faults": faults,
        "analysis_exists": int(analysis_exists),
        "analysis_path": str(analysis_path),
        "overlay_path": overlay_path,
    })

with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    writer.writeheader()
    writer.writerows(out_rows)

print(f"[OK] wrote: {out_path}")
