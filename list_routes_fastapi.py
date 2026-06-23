import re
import os

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

# Regular expression to match route decorators
# e.g., @app.get("/api/cases") or @app.post("/cases/{case_id}")
pattern = r'@app\.(get|post|put|delete|patch)\("([^"]+)"\)'

matches = re.findall(pattern, content)
print("=== ENDPOINTS MATCHED VIA REGEX ===")
for method, path in matches:
    print(f"  Method: {methods_map.get(method, method.upper()):<6} | Path: {path}")

print(f"\nTotal matched: {len(matches)}")
