import sqlalchemy
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

try:
    engine = create_engine(URL_EMDECOB)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id, name FROM project_lists WHERE id = 1")).fetchone()
        if row:
            print(f"List 1 exists: ID={row[0]}, Name={row[1]}")
        else:
            print("List 1 DOES NOT exist in project_lists!")
            
        # Let's find some lists that do exist and their IDs
        rows = conn.execute(text("SELECT id, name FROM project_lists LIMIT 5")).fetchall()
        print("First 5 lists:")
        for r in rows:
            print(f"  ID={r[0]} | Name={r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
