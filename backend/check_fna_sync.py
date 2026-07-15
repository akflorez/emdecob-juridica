import sys
from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding='utf-8')

url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        print("=== CHECKING FNA_JURIDICA SYNC_WITH_CLICKUP ===")
        user = conn.execute(text("SELECT id, username, sync_with_clickup, is_admin, company_id FROM users WHERE username = 'fna_juridica'")).first()
        if user:
            print(f"ID: {user[0]} | User: {user[1]} | SyncWithClickUp: {user[2]} | Admin: {user[3]} | CompanyID: {user[4]}")
            
except Exception as e:
    print(f"Error: {e}")
