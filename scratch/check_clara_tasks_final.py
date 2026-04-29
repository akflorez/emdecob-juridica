
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        for lid in [5046, 6313]:
            res = conn.execute(text("SELECT id, title, status FROM tasks WHERE list_id = :lid"), {"lid": lid}).fetchall()
            print(f"Tasks for List {lid}: {len(res)}")
            for r in res:
                print(f"- {r[1]} | Status: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
