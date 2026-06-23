"""
Fix: rename all /api/admin/* and /api/admin/billing/* routes in backend/main.py
to /admin/* and /billing/* (without /api/ prefix) so they match what NGINX passes.

NGINX strips /api/ from all requests:
  frontend: /api/admin/companies -> NGINX -> backend: /admin/companies
  But backend currently has: /api/admin/companies -> 404!
  
Fix: backend should have /admin/companies (no /api/ prefix)
"""

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ('/api/admin/billing/simulator', '/admin/billing/simulator'),
    ('/api/admin/billing/tiers', '/admin/billing/tiers'),
    ('/api/admin/companies/{company_id}/mark-overdue', '/admin/companies/{company_id}/mark-overdue'),
    ('/api/admin/companies/{company_id}/reactivate', '/admin/companies/{company_id}/reactivate'),
    ('/api/admin/companies/{company_id}/suspend', '/admin/companies/{company_id}/suspend'),
    ('/api/admin/companies', '/admin/companies'),
    ('/api/admin/users', '/admin/users'),
    ('/api/v1/system/health', '/v1/system/health'),
]

for old, new in replacements:
    count = content.count(f'"{old}"')
    if count > 0:
        content = content.replace(f'"{old}"', f'"{new}"')
        print(f'Replaced {count}x: "{old}" -> "{new}"')
    else:
        print(f'NOT FOUND: "{old}"')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\nDone!')
