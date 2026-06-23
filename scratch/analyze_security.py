import re

with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

route_pattern = re.compile(r'@app\.(get|post|put|delete|patch)\("([^"]+)"\)')

results = []
for i, line in enumerate(lines):
    match = route_pattern.search(line)
    if match:
        method = match.group(1).upper()
        path = match.group(2)
        
        # Look at the next few lines for the def statement and arguments
        def_line = ""
        depends_info = []
        for j in range(i + 1, min(i + 15, len(lines))):
            curr = lines[j].strip()
            if "def " in curr or def_line:
                def_line += " " + curr
                if "):" in curr or ") ->" in curr:
                    break
        
        # Extract dependencies
        # Common dependencies: get_current_user, get_current_active_user, get_superadmin, require_superadmin, etc.
        dep_matches = re.findall(r'Depends\(([^)]+)\)', def_line)
        depends_info = dep_matches if dep_matches else ["None"]
        
        # Check if the function queries database and respects company_id or filter by company_id
        # Let's inspect the next 40 lines of the function body for company_id checks
        func_body = []
        for k in range(i + 1, min(i + 50, len(lines))):
            func_body.append(lines[k])
        func_text = "".join(func_body)
        
        has_company_filter = "company_id" in func_text
        has_user_filter = "user_id" in func_text
        
        results.append({
            "line": i + 1,
            "method": method,
            "path": path,
            "def": def_line.strip(),
            "dependencies": ", ".join(depends_info),
            "company_filter": has_company_filter,
            "user_filter": has_user_filter
        })

with open("scratch/routes_security.txt", "w", encoding="utf-8") as out:
    out.write(f"{'Line':<6} | {'Method':<6} | {'Path':<50} | {'Dependencies':<40} | {'CompanyFilter':<13} | {'UserFilter':<10}\n")
    out.write("-" * 140 + "\n")
    for r in results:
        out.write(f"{r['line']:<6} | {r['method']:<6} | {r['path']:<50} | {r['dependencies']:<40} | {str(r['company_filter']):<13} | {str(r['user_filter']):<10}\n")

print(f"Analyzed {len(results)} routes.")
