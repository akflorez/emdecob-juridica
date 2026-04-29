
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        rad = "11001400303520200047100"
        res = conn.execute(text("SELECT id, title FROM tasks WHERE title LIKE :r"), {"r": f"%{rad}%"}).fetchall()
        print(f"Tasks matching {rad} in juricob:")
        for r in res:
            print(f"- ID: {r[0]} | Title: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
