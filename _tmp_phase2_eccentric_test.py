from repright.analyser import RepRightAnalyzer

def run_case(path, exercise):
    an = RepRightAnalyzer()
    out = an.analyze(path, exercise)
    reps = out.get("reps", [])
    if not reps:
        return {"n_reps": 0}
    r0 = reps[0]
    return {
        "schema_version": out.get("schema_version"),
        "n_reps": out.get("n_reps"),
        "start": r0.get("start_frame"),
        "peak": r0.get("peak_frame"),
        "end": r0.get("end_frame"),
        "tempo_up": r0.get("tempo_up_sec"),
        "tempo_down": r0.get("tempo_down_sec"),
        "confidence": r0.get("confidence_v1"),
        "faults": r0.get("faults_v1"),
    }

full = run_case(r"C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\Dissertation-Rep-Right\RepRightRepo\data\raw\curl\barbell biceps curl_1.mp4", "curl")
trunc = run_case(r"C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\Dissertation-Rep-Right\RepRightRepo\data\raw\curl\barbell biceps curl_1_TRUNC.mp4", "curl")

print("=== FULL ===")
for k,v in full.items():
    print(f"{k}: {v}")

print("")
print("=== TRUNC ===")
for k,v in trunc.items():
    print(f"{k}: {v}")

if full.get("n_reps",0) and trunc.get("n_reps",0):
    print("")
    print("=== DIFF (TRUNC - FULL) ===")
    print("tempo_down_sec diff:", float(trunc["tempo_down"]) - float(full["tempo_down"]))
    print("end==peak (full):", full["end"] == full["peak"])
    print("end==peak (trunc):", trunc["end"] == trunc["peak"])

