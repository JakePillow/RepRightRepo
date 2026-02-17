import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Adjust if needed
PROCESSED = Path("data/processed")
EX = "deadlift"
STEM = "deadlift_25"

npz_path = PROCESSED / "pose" / EX / f"{STEM}.npz"
metrics_path = PROCESSED / "metrics" / EX / f"{STEM}_metrics.json"

pose = np.load(npz_path)["pose"]  # (T,33,4) x,y,z,vis
# hips: 23,24 ; shoulders: 11,12 ; elbows 13,14 ; wrists 15,16
L_HIP,R_HIP = 23,24
L_SHO,R_SHO = 11,12

hips_y = pose[:, [L_HIP,R_HIP], 1]
hips_v = pose[:, [L_HIP,R_HIP], 3]
sho_y  = pose[:, [L_SHO,R_SHO], 1]
sho_v  = pose[:, [L_SHO,R_SHO], 3]

vmin = 0.5
hips_y[(hips_v < vmin)] = np.nan
sho_y[(sho_v < vmin)] = np.nan

hip = np.nanmean(hips_y, axis=1)
sho = np.nanmean(sho_y, axis=1)
sig = 0.7*hip + 0.3*sho

# simple fill
x = np.arange(len(sig))
mask = np.isfinite(sig)
sig_f = np.interp(x, x[mask], sig[mask])

# smooth
w = 9
sig_s = np.convolve(sig_f, np.ones(w)/w, mode="same")

# load rep boundaries if present
rep_bounds = []
if metrics_path.exists():
    m = json.loads(metrics_path.read_text(encoding="utf-8"))
    rep_bounds = m.get("rep_bounds", [])  # list of [start,end] if you add it later

plt.figure()
plt.plot(sig_s)
for b in rep_bounds:
    s,e = b
    plt.axvspan(s,e, alpha=0.2)
plt.title(f"{EX} {STEM} signal (smoothed)")
plt.show()
