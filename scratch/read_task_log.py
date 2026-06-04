import os

log_path = r"C:\Users\ANA KARINA\.gemini\antigravity\brain\64b236b7-601c-406b-b65e-728e628cbb8b\.system_generated\tasks\task-5183.log"
print(f"Checking log file at: {log_path}")

if os.path.exists(log_path):
    print("Log file exists!")
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        print("--- CONTENT ---")
        print(f.read())
        print("---------------")
else:
    print("Log file does not exist yet.")
    # Check parent directory
    parent = os.path.dirname(log_path)
    if os.path.exists(parent):
        print(f"Parent directory files: {os.listdir(parent)}")
    else:
        print("Parent directory does not exist.")
