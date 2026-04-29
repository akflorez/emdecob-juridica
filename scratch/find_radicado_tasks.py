
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        radicado = "11001418909420260125200"
        print(f"Finding tasks for radicado: {radicado}")
        res = conn.execute(text("""
            SELECT t.id, t.title, l.name, f.name
            FROM tasks t
            JOIN cases c ON t.case_id = c.id
            JOIN project_lists l ON t.list_id = l.id
            JOIN folders f ON l.folder_id = f.id
            WHERE c.radicado = :r
        """), {"r": radicado}).fetchall()
        for r in res:
            print(f"- Task {r[0]}: {r[1]} | List: {r[2]} | Folder: {r[3]}")
            
except Exception as e:
    print(f"Error: {e}")
