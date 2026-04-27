from __future__ import annotations

import argparse
from pathlib import Path

from repright.analyser import RepRightAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-path", required=True)
    parser.add_argument("--exercise", required=True, choices=["bench", "curl", "deadlift", "squat"])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    analyzer = RepRightAnalyzer()
    analyzer.run(Path(args.video_path), args.exercise, out_path=Path(args.out))
    print(f"[OK] wrote {args.out}")


if __name__ == "__main__":
    main()
