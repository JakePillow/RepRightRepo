# Evaluation Harness

Ground truth file: `data/eval/ground_truth.csv`

Schema:
- `video_id,exercise,path,true_reps,notes`
- `path` may be relative or absolute.
- `true_reps` must be an integer.
- Keep this file append-only in normal workflow.

Run evaluation (append rows to results CSV):

```bash
py scripts/evaluate_dataset.py --ground data/eval/ground_truth.csv --out data/eval/results.csv --tag baseline_v0
```

Summarize one tag:

```bash
py scripts/summarize_eval.py --in data/eval/results.csv --tag baseline_v0
```

Outputs:
- `data/eval/summary_<tag>.json`
- `data/eval/summary_<tag>.csv`
