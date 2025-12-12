import argparse
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple


EXERCISES = ["bench", "squat", "curl", "deadlift"]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def compute_summary_and_qc(
    data: Dict[str, Any],
    rom_threshold: float,
    min_reps: int,
) -> Tuple[int, float, float, bool]:
    """
    Derive n_reps, avg_rom, avg_duration_sec and a simple 'valid' flag
    from an existing metrics JSON dict.

    The function is defensive: if some fields are missing, it falls back
    to zeros instead of crashing.
    """
    reps: List[Dict[str, Any]] = data.get("reps", []) or []

    # n_reps: prefer len(reps), fall back to existing n_reps field if any
    n_reps = len(reps)
    if n_reps == 0:
        n_reps = int(data.get("n_reps", 0) or 0)

    roms: List[float] = []
    durations: List[float] = []

    for rep in reps:
        # Try multiple possible keys just in case
        rom_val = rep.get("rom", None)
        if rom_val is None:
            rom_val = rep.get("amplitude", 0.0)
        try:
            roms.append(float(rom_val))
        except (TypeError, ValueError):
            pass

        dur_val = rep.get("duration_sec", None)
        if dur_val is None:
            dur_val = rep.get("duration", None)
        try:
            dur_val_f = float(dur_val)
            if dur_val_f > 0:
                durations.append(dur_val_f)
        except (TypeError, ValueError):
            pass

    avg_rom = float(sum(roms) / len(roms)) if roms else 0.0
    avg_duration = float(sum(durations) / len(durations)) if durations else 0.0

    # Simple QC:
    # - enough reps
    # - ROM not tiny (pose is doing basically nothing)
    enough_reps = n_reps >= min_reps
    amplitude_ok = avg_rom >= rom_threshold

    valid = bool(enough_reps and amplitude_ok)

    return n_reps, avg_rom, avg_duration, valid


def process_exercise(
    exercise: str,
    processed_root: Path,
    rom_threshold: float,
    min_reps: int,
) -> List[Dict[str, Any]]:
    """
    Upgrade all *_metrics.json files for one exercise and
    return rows for the global CSV index.
    """
    metrics_dir = processed_root / "metrics" / exercise
    if not metrics_dir.exists():
        print(f"[WARN] Metrics dir not found for {exercise}: {metrics_dir}")
        return []

    rows: List[Dict[str, Any]] = []

    for json_path in sorted(metrics_dir.glob("*_metrics.json")):
        data = load_json(json_path)

        # Summary + QC
        n_reps, avg_rom, avg_duration, valid = compute_summary_and_qc(
            data, rom_threshold=rom_threshold, min_reps=min_reps
        )

        data["n_reps"] = n_reps
        data["avg_rom"] = avg_rom
        data["avg_duration_sec"] = avg_duration
        data["valid"] = valid

        save_json(json_path, data)

        stem = json_path.stem
        # Remove trailing '_metrics' from the stem if present
        if stem.endswith("_metrics"):
            video_stem = stem[: -len("_metrics")]
        else:
            video_stem = stem

        row = {
            "exercise": exercise,
            "video_stem": video_stem,
            "metrics_path": str(json_path),
            "n_frames": data.get("n_frames", ""),
            "n_reps": n_reps,
            "avg_rom": avg_rom,
            "avg_duration_sec": avg_duration,
            "valid": int(valid),
        }
        rows.append(row)

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade metrics JSON with summary fields and build a dataset index CSV."
    )
    parser.add_argument(
        "--processed-root",
        default="data/processed",
        help="Root folder that contains pose/ and metrics/ subfolders.",
    )
    parser.add_argument(
        "--index-out",
        default="data/processed/metrics_index.csv",
        help="Path to the CSV index to write.",
    )
    parser.add_argument(
        "--rom-threshold",
        type=float,
        default=0.01,
        help="Minimum average ROM to consider a set valid.",
    )
    parser.add_argument(
        "--min-reps",
        type=int,
        default=1,
        help="Minimum number of reps to consider a set valid.",
    )

    args = parser.parse_args()

    processed_root = Path(args.processed_root)
    index_path = Path(args.index_out)

    all_rows: List[Dict[str, Any]] = []

    for ex in EXERCISES:
        print(f"[INFO] Processing exercise: {ex}")
        rows = process_exercise(
            exercise=ex,
            processed_root=processed_root,
            rom_threshold=args.rom_threshold,
            min_reps=args.min_reps,
        )
        all_rows.extend(rows)
        print(f"[INFO]  {len(rows)} metric files updated for {ex}")

    if all_rows:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with index_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "exercise",
                    "video_stem",
                    "metrics_path",
                    "n_frames",
                    "n_reps",
                    "avg_rom",
                    "avg_duration_sec",
                    "valid",
                ],
            )
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"[INFO] Wrote index CSV with {len(all_rows)} rows to {index_path}")
    else:
        print("[WARN] No metric files found; index CSV not written.")


if __name__ == "__main__":
    main()
