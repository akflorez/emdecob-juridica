import os

def read_file_safe(path):
    if not os.path.exists(path):
        print(f"File {path} not found")
        return
    
    encodings = ['utf-16', 'utf-16-le', 'utf-8', 'latin-1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"Successfully read {path} with encoding {enc}:")
            print(content[:600])
            return
        except Exception as e:
            pass
    print(f"Failed to read {path} with any encoding.")

read_file_safe("backend_startup_debug.log")
read_file_safe("server_debug.log")
