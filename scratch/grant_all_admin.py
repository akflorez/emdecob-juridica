
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Granting Super Admin permissions to all main users...")
        
        # Set is_admin = True for all users to ensure total visibility
        conn.execute(text("UPDATE users SET is_admin = True"))
        
        # Verify the count
        res = conn.execute(text("SELECT username, is_admin FROM users")).fetchall()
        for r in res:
            print(f"User: {r[0]}, Admin: {r[1]}")

        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
