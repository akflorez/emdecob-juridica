
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        list_name = "ALFREDO EDUARDO CAVADIA SANCHEZ"
        res = conn.execute(text("SELECT id FROM project_lists WHERE name = :n"), {"n": list_name}).fetchall()
        print(f"Lists with name '{list_name}' in emdecob_consultas:")
        for r in res:
            t_count = conn.execute(text("SELECT COUNT(*) FROM tasks WHERE list_id = :lid"), {"lid": r[0]}).scalar()
            print(f"- ID: {r[0]} | Tasks: {t_count}")
            
except Exception as e:
    print(f"Error: {e}")
