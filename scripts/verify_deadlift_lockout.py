from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_deadlift_runs(ground_csv: Path, runs_root: Path) -> list[Path]:
    df = pd.read_csv(ground_csv)
    dead = df[df["exercise"].astype(str).str.lower() == "deadlift"].copy()
    names = set(dead.get("video", pd.Series(dtype=str)).astype(str).tolist()) | set(
        dead.get("video_id", pd.Series(dtype=str)).astype(str).tolist()
    )
    names = {n for n in names if n and n != "nan"}

    candidates: list[Path] = []
    for p in runs_root.rglob("analysis_v1.json"):
        s = str(p).lower()
        if "deadlift" in s:
            candidates.append(p)
            continue
        if any(n.lower().replace(".mp4", "") in s for n in names):
            candidates.append(p)
    return sorted(set(candidates))


def get_nested(d: Any, *keys: str) -> Any:
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def find_driver_series(analysis: dict[str, Any], analysis_path: Path) -> np.ndarray | None:
    candidates: list[Path] = []
    metrics_path = analysis.get("metrics_path") or get_nested(analysis, "artifacts_v1", "metrics_path")
    if metrics_path:
        p = Path(metrics_path)
        if not p.is_absolute():
            p = (analysis_path.parent / p).resolve()
        candidates.append(p)

    for name in ["rep_metrics.json", "rep_metrics.jsonl", "metrics.json", "metrics.jsonl", "angles.json", "angles.jsonl"]:
        candidates.extend(analysis_path.parent.rglob(name))

    for p in candidates:
        if not p.exists():
            continue
        try:
            if p.suffix == ".json":
                obj = load_json(p)
                for key_path in [
                    ("angles", "driver"),
                    ("angles", "driver_signal"),
                    ("driver",),
                    ("driver_signal",),
                ]:
                    cur = obj
                    for k in key_path:
                        if isinstance(cur, dict) and k in cur:
                            cur = cur[k]
                        else:
                            cur = None
                            break
                    if isinstance(cur, list) and cur:
                        return np.asarray(cur, dtype=float)
            elif p.suffix == ".jsonl":
                rows = []
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        rows.append(json.loads(line))
                if rows and isinstance(rows[0], dict):
                    for key in ["driver", "driver_signal"]:
                        if key in rows[0]:
                            vals = [r.get(key) for r in rows]
                            return np.asarray(vals, dtype=float)
        except Exception:
            continue
    return None


def classify_peak_orientation(signal: np.ndarray, idx: int, radius: int = 5) -> str:
    left = max(0, idx - radius)
    right = min(len(signal), idx + radius + 1)
    window = signal[left:right]
    if len(window) < 3:
        return "unknown"
    local_max = int(np.argmax(window)) + left
    local_min = int(np.argmin(window)) + left
    if abs(local_max - idx) <= 1:
        return "top"
    if abs(local_min - idx) <= 1:
        return "bottom"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground", required=True)
    parser.add_argument("--runs-root", default="runs")
    args = parser.parse_args()

    ground = Path(args.ground)
    runs_root = Path(args.runs_root)
    if not ground.exists():
        print(f"ERROR: ground truth CSV not found: {ground}")
        return 2
    if not runs_root.exists():
        print(f"ERROR: runs root not found: {runs_root}")
        return 2

    run_paths = find_deadlift_runs(ground, runs_root)
    if not run_paths:
        print("ERROR: no deadlift analysis_v1.json files found under runs root")
        return 2

    total = 0
    top_like = 0
    bottom_like = 0
    unknown = 0

    for ap in run_paths:
        try:
            analysis = load_json(ap)
        except Exception as e:
            print(f"WARN: could not read {ap}: {e}")
            continue

        ex = str(analysis.get("exercise", "")).lower()
        if ex and ex != "deadlift":
            continue

        signal = find_driver_series(analysis, ap)
        if signal is None or len(signal) == 0:
            print(f"WARN: no driver series found for {ap}")
            unknown += 1
            continue

        reps = analysis.get("reps") or []
        if not isinstance(reps, list) or not reps:
            print(f"WARN: no reps array found for {ap}")
            unknown += 1
            continue

        for rep in reps:
            if not isinstance(rep, dict):
                continue
            idx = rep.get("peak_frame")
            if idx is None:
                continue
            idx = int(idx)
            total += 1
            cls = classify_peak_orientation(signal, idx)
            if cls == "top":
                top_like += 1
            elif cls == "bottom":
                bottom_like += 1
            else:
                unknown += 1

    print(f"Deadlift peak orientation summary: total={total}, top={top_like}, bottom={bottom_like}, unknown={unknown}")
    if total == 0:
        print("ERROR: no deadlift rep peak_frame values could be validated")
        return 2
    if bottom_like > 0 and bottom_like >= top_like:
        print("FAIL: deadlift segmentation still appears bottom-anchored")
        return 1
    print("PASS: deadlift segmentation appears lockout/top-anchored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
