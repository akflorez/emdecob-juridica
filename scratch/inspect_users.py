from sqlalchemy import create_engine, text
import json

url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT id, username, email, nombre, company_id, is_admin, is_superadmin, role, is_active FROM users ORDER BY id;"))
    columns = res.keys()
    users = [dict(zip(columns, row)) for row in res]
    print(json.dumps(users, indent=2))
