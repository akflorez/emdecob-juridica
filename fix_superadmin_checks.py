"""
Replace all manual superadmin checks in admin endpoints with is_superadmin() helper.
Old: if current_user.company_id is not None: raise 403
New: if not is_superadmin(current_user): raise 403
"""

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

OLD = '    if current_user.company_id is not None:\n        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")'
NEW = '    if not is_superadmin(current_user):\n        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")'

count = content.count(OLD)
print(f"Found {count} instances of old check")

content = content.replace(OLD, NEW)

# Also fix the /admin/billing endpoints which use the same check
OLD2 = '    if current_user.company_id is not None:\n        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para Superadmin.")'
# already replaced above

# Also fix any variant: "Acceso denegado."
OLD3 = '    if current_user.company_id is not None:\n        raise HTTPException(status_code=403, detail="Acceso denegado.")'
NEW3 = '    if not is_superadmin(current_user):\n        raise HTTPException(status_code=403, detail="Acceso denegado.")'
count3 = content.count(OLD3)
print(f"Found {count3} instances of old check (variant 2)")
content = content.replace(OLD3, NEW3)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
