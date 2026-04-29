
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Resetting admin password...")
        conn.execute(text("UPDATE users SET password = 'admin123' WHERE username = 'admin'"))
        conn.commit()
        print("Done.")
            
except Exception as e:
    print(f"Error: {e}")
