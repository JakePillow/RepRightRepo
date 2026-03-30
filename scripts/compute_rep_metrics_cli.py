from __future__ import annotations

import argparse


DEPRECATION_MESSAGE = (
    "scripts/compute_rep_metrics_cli.py is deprecated and out of sync with the current metrics pipeline. "
    "Use the canonical path repright/analyzer.py -> scripts/pipeline.py -> scripts/extract_all.py -> "
    "scripts/compute_rep_metrics.py instead."
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Deprecated metrics CLI wrapper.")
    ap.add_argument("--npz")
    ap.add_argument("--exercise")
    ap.add_argument("--meta", default=None)
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--out", default=None)
    ap.parse_args()
    raise SystemExit(DEPRECATION_MESSAGE)


if __name__ == "__main__":
    main()
