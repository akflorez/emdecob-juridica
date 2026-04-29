
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT user_id FROM cases WHERE id = 2922")).first()
        print(f"Case 2922 owner (user_id): {res[0]}")
        
        # List users
        res = conn.execute(text("SELECT id, username FROM users")).fetchall()
        print("Users in DB:")
        for r in res:
            print(f"- {r[1]} (ID: {r[0]})")
except Exception as e:
    print(f"Error: {e}")
