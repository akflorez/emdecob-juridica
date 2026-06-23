def try_read(path):
    encodings = ['utf-8', 'utf-16', 'utf-16-le', 'latin-1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
                print(f"--- SUCCESS {path} with {enc} (first 500 chars) ---")
                print(content[:500])
                return
        except Exception as e:
            pass
    print(f"Failed to read {path}")

try_read("backend_startup_debug.log")
try_read("last_logs.txt")
