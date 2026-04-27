from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repright.analyser import RepRightAnalyzer


ACTIVE_FAULT_CODES = (
    "FORWARD_LEAN",
    "INCOMPLETE_EXTENSION",
    "INSUFFICIENT_DEPTH",
    "LOW_ROM",
    "MOMENTUM_SWING",
    "WEAK_EXTENSION",
)

FAULT_MAP = {
    "partial_rom": "LOW_ROM",
    "depth_fail": "LOW_ROM",
    "low_rom": "LOW_ROM",
    "weak_extension": "WEAK_EXTENSION",
    "insufficient_depth": "INSUFFICIENT_DEPTH",
    "forward_lean": "FORWARD_LEAN",
    "momentum_swing": "MOMENTUM_SWING",
    "incomplete_extension": "INCOMPLETE_EXTENSION",
}


def _norm_key(k: str) -> str:
    return (k or "").replace("\ufeff", "").strip().lower()


def _read_label_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rr = {_norm_key(k): v for k, v in (r or {}).items()}
            rows.append(rr)
    return rows


def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _truth_fault_codes(row: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for k in ("error_primary", "error_secondary"):
        lab = (row.get(k) or "").strip().lower()
        if not lab or lab == "none":
            continue
        code = FAULT_MAP.get(lab)
        if code:
            out.add(code)
    return out


def _has_any_fault_label(row: dict[str, Any]) -> bool:
    for k in ("error_primary", "error_secondary"):
        lab = (row.get(k) or "").strip().lower()
        if lab and lab != "none":
            return True
    return False


def _fault_eval_row_usable(row: dict[str, Any]) -> bool:
    for k in ("error_primary", "error_secondary"):
        lab = (row.get(k) or "").strip().lower()
        if not lab or lab == "none":
            continue
        if lab not in FAULT_MAP:
            return False
    return True


def _pred_fault_codes(analysis: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    for rep in analysis.get("reps", []) or []:
        for f in rep.get("faults_v1", []) or []:
            if isinstance(f, dict) and f.get("code"):
                code = str(f["code"])
                if code in ACTIVE_FAULT_CODES:
                    codes.add(code)
    return codes


def _resolve_video(repo_root: Path, video_path: str) -> str:
    p = Path(video_path)
    if p.is_absolute():
        return str(p)
    return str((repo_root / p).resolve())


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json(p: Path, obj: dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")


@dataclass
class RepCountRow:
    video_id: str
    exercise: str
    expected: int
    predicted: int
    abs_error: int
    analysis_path: str


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--max-videos", type=int, default=0)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(args.repo_root).resolve()

    analyzer = RepRightAnalyzer()

    repcount_rows: list[RepCountRow] = []

    counts: dict[str, dict[str, int]] = {code: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for code in ACTIVE_FAULT_CODES}
    fault_count_per_video_rows: list[tuple[str, str, int]] = []
    fault_rate_per_exercise: dict[str, dict[str, int]] = {}
    fault_summary_by_exercise: dict[tuple[str, str], int] = {}

    total_sets = 0
    exact_match_sets = 0
    abs_errors: list[int] = []

    processed_videos = 0

    runs_root = outdir / "runs"

    rows = _read_label_rows(Path(args.labels))
    print(f"[EVAL] Using {len(rows)} labeled videos")

    valid_rows = 0
    has_ground_truth_fault_labels = any(_truth_fault_codes(r) for r in rows)

    for row in rows:

        video_id = (row.get("video_id") or "").strip()
        exercise = (row.get("exercise") or "").strip().lower()
        video_path = (row.get("path") or "").strip()
        expected = _as_int(row.get("true_reps"), default=0)

        if not video_path or not video_id or exercise not in {"bench", "curl", "deadlift", "squat"}:
            continue

        video_raw = Path(video_path)
        if not video_raw.exists():
            print(f"[WARN] missing video: {video_path}")
            continue

        valid_rows += 1

        video_abs = _resolve_video(repo_root, video_path)

        analysis_path = runs_root / exercise / video_id / "analysis_v1.json"

        if analysis_path.exists():
            analysis = _load_json(analysis_path)
        else:
            analysis = analyzer.run(video_abs, exercise, out_path=str(analysis_path.parent))
            _save_json(analysis_path, analysis)

        predicted = int(len(analysis.get("reps") or []))
        abs_err = abs(predicted - expected)

        repcount_rows.append(
            RepCountRow(
                video_id=video_id,
                exercise=exercise,
                expected=expected,
                predicted=predicted,
                abs_error=abs_err,
                analysis_path=str(analysis_path),
            )
        )

        total_sets += 1
        abs_errors.append(abs_err)

        if predicted == expected:
            exact_match_sets += 1

        truth = _truth_fault_codes(row)
        pred = _pred_fault_codes(analysis)
        n_faults_this_video = 0
        for rep in analysis.get("reps", []) or []:
            rep_faults = rep.get("faults_v1", []) or []
            for f in rep_faults:
                if not isinstance(f, dict):
                    continue
                code = str(f.get("code") or "")
                if code not in ACTIVE_FAULT_CODES:
                    continue
                n_faults_this_video += 1
                fault_summary_by_exercise[(exercise, code)] = fault_summary_by_exercise.get((exercise, code), 0) + 1

        fault_count_per_video_rows.append((video_id, exercise, int(n_faults_this_video)))
        rates = fault_rate_per_exercise.setdefault(exercise, {"videos": 0, "videos_with_faults": 0, "fault_count_total": 0})
        rates["videos"] += 1
        rates["fault_count_total"] += int(n_faults_this_video)
        if n_faults_this_video > 0:
            rates["videos_with_faults"] += 1

        if has_ground_truth_fault_labels and _fault_eval_row_usable(row):
            for code in ACTIVE_FAULT_CODES:
                c = counts.setdefault(code, {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
                t = code in truth
                p = code in pred

                if t and p:
                    c["tp"] += 1
                elif (not t) and p:
                    c["fp"] += 1
                elif t and (not p):
                    c["fn"] += 1
                else:
                    c["tn"] += 1

        processed_videos += 1

        if args.max_videos and processed_videos >= args.max_videos:
            break

    mae = (sum(abs_errors) / len(abs_errors)) if abs_errors else 0.0
    rmse = ((sum((e * e) for e in abs_errors) / len(abs_errors)) ** 0.5) if abs_errors else 0.0
    exact_pct = (exact_match_sets / total_sets * 100.0) if total_sets else 0.0

    summary = {
        "schema_version": "eval_v1",
        "n_sets": total_sets,
        "repcount": {
            "mae": mae,
            "rmse": rmse,
            "exact_match_pct": exact_pct,
        },
        "faults_evaluated": list(ACTIVE_FAULT_CODES),
    }

    _save_json(outdir / "eval_summary.json", summary)

    with (outdir / "eval_repcount.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "exercise", "expected_reps", "predicted_reps", "abs_error", "analysis_path"])

        for r in repcount_rows:
            w.writerow(
                [
                    r.video_id,
                    r.exercise,
                    r.expected,
                    r.predicted,
                    r.abs_error,
                    r.analysis_path,
                ]
            )

    with (outdir / "eval_faults.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if has_ground_truth_fault_labels:
            w.writerow(["fault_code", "tp", "fp", "fn", "tn", "precision", "recall", "f1"])
            for code, c in counts.items():
                tp, fp, fn = c["tp"], c["fp"], c["fn"]

                precision = tp / (tp + fp) if (tp + fp) else 0.0
                recall = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

                w.writerow([code, tp, fp, fn, c["tn"], precision, recall, f1])
        else:
            w.writerow(["exercise", "video_id", "fault_count_per_video", "fault_rate_per_exercise"])
            for video_id, exercise, fault_count in fault_count_per_video_rows:
                rates = fault_rate_per_exercise.get(exercise) or {}
                videos = int(rates.get("videos", 0))
                videos_with_faults = int(rates.get("videos_with_faults", 0))
                fault_rate = (videos_with_faults / videos) if videos else 0.0
                w.writerow([exercise, video_id, fault_count, fault_rate])

    fault_summary_path = outdir / "fault_summary_by_exercise.csv"
    with fault_summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["exercise", "fault_code", "count", "avg_per_video"])
        for (exercise, code), count in sorted(fault_summary_by_exercise.items()):
            rates = fault_rate_per_exercise.get(exercise) or {}
            videos = int(rates.get("videos", 0))
            avg_per_video = (float(count) / videos) if videos else 0.0
            w.writerow([exercise, code, int(count), avg_per_video])

    if valid_rows > 0 and total_sets <= 0:
        raise RuntimeError("n_sets must be > 0 when valid videos exist")

    print(f"[OK] wrote: {outdir/'eval_summary.json'}")
    print(f"[OK] wrote: {outdir/'eval_repcount.csv'}")
    print(f"[OK] wrote: {outdir/'fault_summary_by_exercise.csv'}")
    print(f"[OK] wrote: {outdir/'eval_faults.csv'}")
    if processed_videos != valid_rows:
        raise RuntimeError(f"processed_videos mismatch: processed={processed_videos} valid_rows={valid_rows}")
    print(f"[DBG] processed_videos={processed_videos} n_sets={total_sets}")


if __name__ == "__main__":
    main()
