from pathlib import Path
import json

INPUT_DIR = Path("data/processed/runs")
OUTPUT_DIR = Path("data/eval/form_examples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def find_analysis_files():
    return list(INPUT_DIR.rglob("analysis_v1.json"))

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def extract_example(data):
    reps = data.get("reps", [])
    if not reps:
        return None

    example = {
        "video_id": data.get("video_id"),
        "exercise": data.get("exercise"),
        "rep_metrics": []
    }

    for r in reps:
        example["rep_metrics"].append({
            "rep_index": r.get("rep_index"),
            "rom": r.get("rom"),
            "tempo_up_sec": r.get("tempo_up_sec"),
            "tempo_down_sec": r.get("tempo_down_sec"),
            "faults": r.get("faults_v1"),
            "confidence": r.get("confidence_v1")
        })

    return example

def main():
    files = find_analysis_files()

    by_exercise = {}

    for f in files:
        data = load_json(f)
        if not data:
            continue

        ex = data.get("exercise")
        reps = data.get("reps", [])

        if not ex or not reps:
            continue

        # keep the file with the most reps as the example
        if ex not in by_exercise:
            by_exercise[ex] = (len(reps), f)
        else:
            if len(reps) > by_exercise[ex][0]:
                by_exercise[ex] = (len(reps), f)

    for exercise, (_, file) in by_exercise.items():
        data = load_json(file)
        example = extract_example(data)

        if example:
            out = OUTPUT_DIR / f"{exercise}_example.json"
            out.write_text(json.dumps(example, indent=2))
            print("exported:", out)

if __name__ == "__main__":
    main()