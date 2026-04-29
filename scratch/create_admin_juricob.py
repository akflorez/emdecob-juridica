
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Creating admin user in juricob...")
        
        # Check if admin already exists (maybe I missed it)
        exists = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
        if not exists:
            # We use a high ID for admin to avoid conflicts with 1 and 2
            # But wait! The code might use ID as an integer.
            # In emdecob_consultas it was ID 2.
            # In juricob ID 2 is already taken.
            # I'll use ID 3.
            conn.execute(text("INSERT INTO users (id, username, password, role, is_admin, created_at) VALUES (3, 'admin', 'admin123', 'admin', True, NOW())"))
            print("Admin user created with ID 3")
        else:
            conn.execute(text("UPDATE users SET is_admin = True WHERE username = 'admin'"))
            print("Admin user updated to is_admin=True")
            
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
