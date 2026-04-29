from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


# Canonical pipeline entrypoint (code-only, stable artifacts)
from scripts.pipeline import run_full_pipeline


@dataclass
class RepRightAnalyzer:
    processed_root: Path = Path("data/processed")
    uploads_root: Path = Path("data/uploads")
    python_exe: Optional[str] = None  # kept for compatibility (pipeline may not need it)

    def _stage_upload(self, video_path: Path, exercise: str) -> Path:
        """
        Copy to uploads/ with an exercise-tagged filename so downstream inference is stable.
        """
        video_path = Path(video_path)
        ex = (exercise or "").strip().lower()
        self.uploads_root.mkdir(parents=True, exist_ok=True)

        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe_stem = video_path.stem.replace(" ", "_")
        out_name = f"{stamp}_{ex}_{safe_stem}{video_path.suffix}"
        out_path = self.uploads_root / out_name

        if video_path.resolve() != out_path.resolve():
            out_path.write_bytes(video_path.read_bytes())

        return out_path

    def _load_json(self, p: Path) -> Dict[str, Any]:
        return json.loads(p.read_text(encoding="utf-8"))

    def _run_pipeline(self, staged: Path, exercise: str, run_dir: Path | None = None) -> Any:
        try:
            return run_full_pipeline(
                video_path=str(staged),
                exercise=exercise,
                run_dir=str(run_dir) if run_dir is not None else None,
                processed_root=str(self.processed_root),
            )
        except TypeError:
            try:
                return run_full_pipeline(
                    str(staged),
                    exercise,
                    str(run_dir) if run_dir is not None else None,
                    processed_root=str(self.processed_root),
                )
            except TypeError:
                if run_dir is not None:
                    try:
                        return run_full_pipeline(
                            str(staged),
                            exercise,
                            run_dir=str(run_dir),
                            processed_root=str(self.processed_root),
                        )
                    except TypeError:
                        pass
                return run_full_pipeline(str(staged), exercise, processed_root=str(self.processed_root))

    def analyze(
        self,
        video_path: str,
        exercise: str,
        *,
        run_dir: Path | None = None,
        out_path: Path | None = None,
    ) -> Dict[str, Any]:
        """
        Returns locked analysis_v1 dict (including artifacts_v1.overlay_path if valid).
        """
        ex = (exercise or "").strip().lower()
        vp = Path(video_path)

        staged = self._stage_upload(vp, ex)

        # ---- Run canonical pipeline (signature-flexible) ----
        result: Any = self._run_pipeline(staged, ex, run_dir=run_dir)

        # ---- Normalize outputs ----
        # We support any of:
        # - dict (analysis)
        # - tuple like (analysis_json_path, analysis_dict)
        # - tuple like (analysis_dict, analysis_json_path)
        # - tuple with run_dir etc
        analysis: Optional[Dict[str, Any]] = None
        analysis_json_path: Optional[Path] = None

        if isinstance(result, dict):
            analysis = result
        elif isinstance(result, (list, tuple)):
            # search for dict + path-ish
            for item in result:
                if isinstance(item, dict) and analysis is None:
                    analysis = item
                if isinstance(item, (str, Path)):
                    p = Path(item)
                    if p.suffix.lower() == ".json" and analysis_json_path is None:
                        analysis_json_path = p

        # If we got a json path but not dict, load it
        if analysis is None and analysis_json_path is not None and analysis_json_path.exists():
            analysis = self._load_json(analysis_json_path)

        if analysis is None:
            raise RuntimeError("Pipeline did not return analysis dict or readable analysis json path.")

        # Ensure expected schema marker
        # (don't overwrite if pipeline already sets it)
        if "schema_version" not in analysis:
            analysis["schema_version"] = "analysis_v1"

        # Ensure video_path points to staged input (useful for UI)
        analysis.setdefault("video_path", str(staged).replace("\\", "/"))
        analysis.setdefault("exercise", ex)

        if out_path is not None and out_path.suffix.lower() == ".json":
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

        return analysis

    # Backward compatibility for older UI code that calls analyzer.run(...)
    def run(self, video_path: str | Path, exercise: str, **kwargs: Any) -> Dict[str, Any]:
        options = kwargs.get("options")
        run_dir = kwargs.get("run_dir")
        out_path = kwargs.get("out_path")

        if isinstance(options, dict):
            run_dir = run_dir or options.get("run_dir")
            out_path = out_path or options.get("out_path")

        run_dir_p = Path(run_dir) if run_dir else None
        out_path_p = Path(out_path) if out_path else None

        if run_dir_p is None and out_path_p is not None and out_path_p.suffix.lower() != ".json":
            run_dir_p = out_path_p
            out_path_p = None

        return self.analyze(str(video_path), exercise, run_dir=run_dir_p, out_path=out_path_p)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="RepRight Analyzer (single-pipeline entrypoint).")
    ap.add_argument("--video", required=True, help="Path to input video")
    ap.add_argument("--exercise", required=True, help="Exercise label (curl, bench, squat, deadlift, ...)")
    ap.add_argument("--processed-root", default="data/processed", help="Processed output root")
    ap.add_argument("--uploads-root", default="data/uploads", help="Uploads staging root")
    ap.add_argument("--out", default=None, help="Optional path to write analyser output JSON")
    args = ap.parse_args()

    analyzer = RepRightAnalyzer(
        processed_root=Path(args.processed_root),
        uploads_root=Path(args.uploads_root),
    )

    result = analyzer.analyze(args.video, args.exercise)

    overlay = (result.get("artifacts_v1") or {}).get("overlay_path") or result.get("overlay_path") or ""
    metrics = (result.get("artifacts_v1") or {}).get("metrics_path") or result.get("metrics_path") or ""
    n_reps = (result.get("set_summary_v1") or {}).get("n_reps", result.get("n_reps"))

    if metrics:
        print(str(metrics).replace("\\", "/"))
    if overlay:
        print(str(overlay).replace("\\", "/"))
    print(f"n_reps={n_reps}")

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
