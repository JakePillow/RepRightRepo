from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LABELS_ROOT = REPO_ROOT / "data" / "labels"
RAW_ROOT = REPO_ROOT / "data" / "raw-Jakes_PC"
OUT_PATH = REPO_ROOT / "data" / "eval" / "ground_truth.csv"

CANDIDATES = [
    LABELS_ROOT / "bench_labels.csv",
    LABELS_ROOT / "curl_labels.csv",
    LABELS_ROOT / "deadlift_labels.csv",
    LABELS_ROOT / "squat_labels.csv",
]


def norm_video_id(video_rel: str) -> str:
    return Path(str(video_rel).strip()).stem.strip()


def norm_exercise(row: dict, fallback_name: str) -> str:
    ex = str(row.get("exercise") or "").strip().lower()
    if ex:
        return ex
    return fallback_name.replace("_labels", "").replace(".csv", "").strip().lower()


def norm_true_reps(v) -> int:
    s = str(v).strip()
    if s == "":
        raise ValueError("missing expected_reps")
    return int(float(s))


def resolve_real_path(video_rel: str) -> str:
    """
    Convert label path like:
      data/raw/bench/bench press_1.mp4
    into the actual dataset location under raw-Jakes_PC.

    Strategy:
    1) try exact relative suffix after data/raw/
    2) fallback to filename search under raw-Jakes_PC
    """
    raw = str(video_rel).strip().replace("\\", "/")
    p = Path(raw)

    # If already absolute and exists, keep it
    if p.is_absolute() and p.exists():
        return str(p)

    # Try to strip leading data/raw/
    parts = list(p.parts)
    lowered = [str(x).lower() for x in parts]

    if "data" in lowered and "raw" in lowered:
        i_data = lowered.index("data")
        i_raw = lowered.index("raw", i_data + 1)
        suffix_parts = parts[i_raw + 1 :]
        candidate = RAW_ROOT.joinpath(*suffix_parts)
        if candidate.exists():
            return str(candidate)

    # Also try just relative after raw/
    if "raw" in lowered:
        i_raw = lowered.index("raw")
        suffix_parts = parts[i_raw + 1 :]
        candidate = RAW_ROOT.joinpath(*suffix_parts)
        if candidate.exists():
            return str(candidate)

    # Fallback: search by filename only
    matches = list(RAW_ROOT.rglob(p.name))
    if len(matches) == 1:
        return str(matches[0])

    # If multiple or none, just return the original raw string
    return raw


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows_out: list[dict[str, str | int]] = []
    seen: set[tuple[str, str]] = set()

    for path in CANDIDATES:
        if not path.exists():
            print(f"[WARN] missing labels file: {path}")
            continue

        print(f"[INFO] reading {path}")
        fallback_name = path.name

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                video_rel = str(row.get("video_rel") or "").strip()
                if not video_rel:
                    continue

                try:
                    true_reps = norm_true_reps(row.get("expected_reps"))
                except Exception:
                    continue

                exercise = norm_exercise(row, fallback_name)
                video_id = norm_video_id(video_rel)
                notes = str(row.get("notes") or "").strip()
                real_path = resolve_real_path(video_rel)

                key = (exercise, video_id)
                if key in seen:
                    continue
                seen.add(key)

                rows_out.append(
                    {
                        "video_id": video_id,
                        "exercise": exercise,
                        "path": real_path,
                        "true_reps": true_reps,
                        "notes": notes,
                    }
                )

    rows_out.sort(key=lambda r: (str(r["exercise"]), str(r["video_id"])))

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video_id", "exercise", "path", "true_reps", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"[OK] wrote {OUT_PATH}")
    print(f"[OK] rows={len(rows_out)}")


if __name__ == "__main__":
    main()