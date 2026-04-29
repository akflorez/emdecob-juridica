
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        users = conn.execute(text("SELECT id, username FROM users")).fetchall()
        print("Users in DB:")
        for u in users:
            print(f"- ID: {u[0]} | Username: {u[1]}")
            
except Exception as e:
    print(f"Error: {e}")
