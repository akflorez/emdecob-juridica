
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Workspaces owner_ids:")
        res = conn.execute(text("SELECT id, name, owner_id FROM workspaces")).fetchall()
        for r in res:
            print(f"- {r[1]} (ID: {r[0]}, Owner: {r[2]})")
            
        print("\nWorkspace Members:")
        res = conn.execute(text("SELECT workspace_id, user_id FROM workspace_members")).fetchall()
        for r in res:
            print(f"- WS: {r[0]}, User: {r[1]}")
            
        print("\nUsers in DB:")
        res = conn.execute(text("SELECT id, username FROM users")).fetchall()
        for r in res:
            print(f"- {r[1]} (ID: {r[0]})")
except Exception as e:
    print(f"Error: {e}")
