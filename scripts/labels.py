from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List, Optional

LABELS_DIR = Path("data/labels")

def load_all_labels() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not LABELS_DIR.exists():
        return rows
    for p in sorted(LABELS_DIR.glob("*.csv")):
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["_labels_file"] = str(p)
                rows.append(r)
    return rows

def get_label_for_video(video_rel: str, exercise: Optional[str] = None) -> Optional[Dict[str, str]]:
    video_rel = video_rel.replace("\\", "/")
    for r in load_all_labels():
        if r.get("video_rel","").replace("\\","/") == video_rel:
            if exercise is None or (r.get("exercise","").lower() == exercise.lower()):
                return r
    return None
