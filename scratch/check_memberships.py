
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT workspace_id, user_id FROM workspace_members")).fetchall()
        print("Workspace memberships in juricob:")
        for r in res:
            print(f"- Workspace: {r[0]} | User: {r[1]}")
            
except Exception as e:
    print(f"Error: {e}")
