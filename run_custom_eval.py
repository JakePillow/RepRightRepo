from pathlib import Path
from repright.analyzer import RepRightAnalyzer
import csv

gt_path = Path(r"data\eval\ground_truth_custom.csv")
src_root = Path(r"data\raw_custom")
out_root = Path(r"data\eval_custom")

rows = list(csv.DictReader(gt_path.open("r", encoding="utf-8-sig")))
analyzer = RepRightAnalyzer()

for row in rows:
    video = row["video"]
    exercise = row["exercise"]
    video_path = src_root / exercise / video
    run_dir = out_root / video.replace(".mp4", "")
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {video} [{exercise}]")
    analyzer.run(
        video_path=str(video_path),
        exercise=exercise,
        out_path=str(run_dir)
    )
