from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _to_float(v: Any) -> float | None:
    try:
        if v is None or str(v).strip() == "":
            return None
        return float(v)
    except Exception:
        return None


def _to_int(v: Any) -> int | None:
    try:
        if v is None or str(v).strip() == "":
            return None
        return int(float(v))
    except Exception:
        return None


def _to_bool(v: Any) -> bool:
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "t"}


def _metrics(rows: list[dict[str, str]]) -> dict[str, float | int]:
    n_videos = len(rows)
    abs_errors = [x for x in (_to_float(r.get("abs_error")) for r in rows) if x is not None]
    rep_errors = [x for x in (_to_float(r.get("rep_error")) for r in rows) if x is not None]

    mae = (sum(abs_errors) / len(abs_errors)) if abs_errors else 0.0
    accuracy_exact = (sum(1 for e in rep_errors if e == 0) / len(rep_errors) * 100.0) if rep_errors else 0.0
    accuracy_pm1 = (sum(1 for e in rep_errors if abs(e) <= 1) / len(rep_errors) * 100.0) if rep_errors else 0.0

    overlay_vals = [_to_int(r.get("overlay_valid")) for r in rows]
    overlay_numeric = [v for v in overlay_vals if v is not None]
    overlay_valid_rate = (sum(1 for v in overlay_numeric if v == 1) / len(overlay_numeric) * 100.0) if overlay_numeric else 0.0

    inversion_rate = (sum(1 for r in rows if _to_bool(r.get("inversion"))) / n_videos * 100.0) if n_videos else 0.0

    return {
        "n_videos": n_videos,
        "mae": mae,
        "accuracy_exact": accuracy_exact,
        "accuracy_pm1": accuracy_pm1,
        "overlay_valid_rate": overlay_valid_rate,
        "inversion_rate": inversion_rate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize evaluation metrics for a tag from results.csv")
    parser.add_argument("--in", dest="in_csv", required=True, help="Path to results.csv")
    parser.add_argument("--tag", required=True, help="Tag to summarize")
    args = parser.parse_args()

    in_path = Path(args.in_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Results file not found: {in_path}")

    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    tagged_rows = [r for r in rows if (r.get("tag") or "") == args.tag]
    overall = _metrics(tagged_rows)

    by_exercise: dict[str, list[dict[str, str]]] = {}
    for row in tagged_rows:
        ex = (row.get("exercise") or "").strip().lower() or "unknown"
        by_exercise.setdefault(ex, []).append(row)

    exercise_summary: dict[str, dict[str, float | int]] = {
        ex: _metrics(ex_rows) for ex, ex_rows in sorted(by_exercise.items())
    }

    output_root = Path("data/eval")
    output_root.mkdir(parents=True, exist_ok=True)

    out_json = output_root / f"summary_{args.tag}.json"
    out_csv = output_root / f"summary_{args.tag}.csv"

    payload = {
        "tag": args.tag,
        "overall": overall,
        "per_exercise": exercise_summary,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "exercise",
            "n_videos",
            "mae",
            "accuracy_exact",
            "accuracy_pm1",
            "overlay_valid_rate",
            "inversion_rate",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"exercise": "ALL", **overall})
        for exercise, metrics in exercise_summary.items():
            writer.writerow({"exercise": exercise, **metrics})

    print(f"Tag: {args.tag}")
    print(f"n_videos={overall['n_videos']}")
    print(f"MAE={overall['mae']:.4f}")
    print(f"accuracy_exact={overall['accuracy_exact']:.2f}%")
    print(f"accuracy_pm1={overall['accuracy_pm1']:.2f}%")
    print(f"overlay_valid_rate={overall['overlay_valid_rate']:.2f}%")
    print(f"inversion_rate={overall['inversion_rate']:.2f}%")
    print("Per-exercise:")
    for exercise, metrics in exercise_summary.items():
        print(
            f"  - {exercise}: n={metrics['n_videos']} "
            f"MAE={metrics['mae']:.4f} "
            f"exact={metrics['accuracy_exact']:.2f}% "
            f"pm1={metrics['accuracy_pm1']:.2f}% "
            f"overlay={metrics['overlay_valid_rate']:.2f}% "
            f"inversion={metrics['inversion_rate']:.2f}%"
        )

    print(f"[OK] wrote: {out_json}")
    print(f"[OK] wrote: {out_csv}")


if __name__ == "__main__":
    main()
