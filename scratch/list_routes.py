import re

routes = []
methods_map = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "delete": "DELETE",
    "patch": "PATCH"
}

with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Match app.get, app.post, etc.
pattern = r'@app\.(get|post|put|delete|patch)\("([^"]+)"\)'
matches = re.findall(pattern, content)

with open("scratch/endpoints.txt", "w", encoding="utf-8") as out:
    out.write("=== ENDPOINTS MATCHED VIA REGEX ===\n")
    for method, path in matches:
        out.write(f"Method: {methods_map.get(method, method.upper()):<6} | Path: {path}\n")
    out.write(f"\nTotal matched: {len(matches)}\n")

print(f"Successfully extracted {len(matches)} routes to scratch/endpoints.txt")
