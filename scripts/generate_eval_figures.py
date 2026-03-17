import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT = Path("data/eval/results_all_lifts.csv")
OUTDIR = Path("data/eval/figures")
OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# -------------------------------
# Rep Error Histogram
# -------------------------------

plt.figure()

df["rep_error"].hist(bins=15)

plt.xlabel("Rep Count Error (Predicted - True)")
plt.ylabel("Number of Videos")
plt.title("Distribution of Rep Count Error")

plt.tight_layout()
plt.savefig(OUTDIR / "rep_error_histogram.png")
plt.close()

print("Saved:", OUTDIR / "rep_error_histogram.png")

# -------------------------------
# Accuracy by Exercise
# -------------------------------

summary = df.groupby("exercise").apply(
    lambda x: pd.Series({
        "exact_accuracy": (x["rep_error"] == 0).mean() * 100,
        "pm1_accuracy": (x["abs_error"] <= 1).mean() * 100
    })
)

plt.figure()

summary.plot(kind="bar")

plt.ylabel("Accuracy (%)")
plt.title("Rep Counting Accuracy by Exercise")

plt.xticks(rotation=0)

plt.tight_layout()
plt.savefig(OUTDIR / "accuracy_by_exercise.png")
plt.close()

print("Saved:", OUTDIR / "accuracy_by_exercise.png")