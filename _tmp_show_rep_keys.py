from repright.analyser import RepRightAnalyzer

VIDEO = r"C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\Dissertation-Rep-Right\RepRightRepo\data\raw\curl\barbell biceps curl_1.mp4"
EX = "curl"

an = RepRightAnalyzer()
out = an.analyze(VIDEO, EX)

r0 = out["reps"][0]
print("keys:", sorted(r0.keys()))
print("tempo_down_sec:", r0.get("tempo_down_sec"))
print("tempo_down_sec_inferred:", r0.get("tempo_down_sec_inferred"))
print("tempo_down_inferred:", r0.get("tempo_down_inferred"))
print("end_frame_source:", r0.get("end_frame_source"))
print("confidence_v1:", r0.get("confidence_v1"))
