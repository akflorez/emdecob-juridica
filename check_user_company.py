from backend.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== DETALLE DEL USUARIO juricob ===")
    u = db.execute(text(
        "SELECT id, username, is_admin, is_superadmin, company_id, cases_view_scope, role, is_active "
        "FROM users WHERE username = 'juricob'"
    )).fetchone()
    if u:
        print(f"  ID:               {u[0]}")
        print(f"  username:         {u[1]}")
        print(f"  is_admin:         {u[2]}")
        print(f"  is_superadmin:    {u[3]}")
        print(f"  company_id:       {u[4]}")
        print(f"  cases_view_scope: {u[5]}")
        print(f"  role:             {u[6]}")
        print(f"  is_active:        {u[7]}")
    else:
        print("  Usuario juricob NO encontrado")

    print()
    print("=== TODOS LOS USUARIOS CON SU SCOPE ===")
    all_u = db.execute(text(
        "SELECT id, username, is_admin, is_superadmin, company_id, cases_view_scope, role "
        "FROM users ORDER BY id"
    )).fetchall()
    for u in all_u:
        print(f"  ID={u[0]:3} | {u[1]:<25} | admin={str(u[2]):<5} | superadmin={str(u[3]):<5} | company={str(u[4]):<6} | scope={u[5]} | role={u[6]}")
finally:
    db.close()
