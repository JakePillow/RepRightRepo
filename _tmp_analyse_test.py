from repright.analyser import RepRightAnalyzer

an = RepRightAnalyzer()
out = an.analyze(r"C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\Dissertation-Rep-Right\RepRightRepo\data\raw\curl\barbell biceps curl_1.mp4", "curl")

print("schema_version:", out.get("schema_version"))
print("exercise:", out.get("exercise"))
print("n_reps:", out.get("n_reps"))
print("metrics_path:", out.get("metrics_path"))
print("overlay_path:", out.get("overlay_path"))

reps = out.get("reps", [])
if reps:
    r0 = reps[0]
    print("first_rep keys:", sorted(list(r0.keys())))
    print("first_rep tempo_down_sec:", r0.get("tempo_down_sec"))
    print("first_rep confidence_v1:", r0.get("confidence_v1"))
    print("first_rep biomech_v1:", r0.get("biomech_v1"))
    print("first_rep faults_v1:", r0.get("faults_v1"))
else:
    print("No reps detected.")
