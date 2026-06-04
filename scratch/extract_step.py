import json
import os

path = r"C:\Users\ANA KARINA\.gemini\antigravity\brain\64b236b7-601c-406b-b65e-728e628cbb8b\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        if data.get("step_index") == 2291:
            rc = data["tool_calls"][0]["args"]["ReplacementContent"]
            with open("scratch/extracted_rc.py", "w", encoding="utf-8") as out:
                out.write(rc)
            print("Extracted rc directly to scratch/extracted_rc.py, size:", len(rc))
            break
