import argparse
import json
from pathlib import Path
import sys

# Make sure we can import engine from scripts/
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts"))

from engine import analyze_video  # type: ignore


def main():
    parser = argparse.ArgumentParser(description="RepRight JSON analyzer")
    parser.add_argument("--exercise", required=True,
                        choices=["bench", "squat", "curl", "deadlift"])
    parser.add_argument("--video", required=True,
                        help="Path to video under data/raw")
    args = parser.parse_args()

    result = analyze_video(args.video, args.exercise)

    json.dump(result, sys.stdout, indent=2)
    print()  # newline


if __name__ == "__main__":
    main()
