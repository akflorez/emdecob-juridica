
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, name, owner_id FROM workspaces")).fetchall()
        print("Workspaces in juricob:")
        for r in res:
            print(f"- ID: {r[0]} | Name: {r[1]} | Owner ID: {r[2]}")
            
except Exception as e:
    print(f"Error: {e}")
