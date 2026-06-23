import re
import os

routes_found = []

# Scan all files in frontend/src
for root, dirs, files in os.walk("frontend/src"):
    for file in files:
        if file.endswith((".ts", ".tsx")):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple regex to find paths like '/api/...' or '/auth/...' or '/cases/...'
            # matches path strings in quotes
            matches = re.findall(r'[\'"`](/api/[^\s\'"`?#]+|/auth/[^\s\'"`?#]+|/cases/[^\s\'"`?#]+|/projects/[^\s\'"`?#]+|/publicaciones/[^\s\'"`?#]+|/search/[^\s\'"`?#]+)[\'"`]', content)
            for m in matches:
                routes_found.append({
                    "file": file,
                    "path": filepath,
                    "endpoint": m
                })

with open("scratch/frontend_endpoints.txt", "w", encoding="utf-8") as out:
    out.write(f"{'File':<30} | {'Endpoint':<70}\n")
    out.write("-" * 110 + "\n")
    for r in sorted(routes_found, key=lambda x: (x['file'], x['endpoint'])):
        out.write(f"{r['file']:<30} | {r['endpoint']:<70}\n")

print(f"Extracted {len(routes_found)} references to endpoints.")
