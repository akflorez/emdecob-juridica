
import sqlalchemy
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        print("Ensuring Admin user with correct permissions in JURICOB...")
        
        # Check if admin exists
        admin = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
        
        hashed = _hash_password("admin123")
        
        if not admin:
            # Create admin with ID 3
            conn.execute(text("""
                INSERT INTO users (id, username, hashed_password, nombre, is_active, is_admin, created_at)
                VALUES (3, 'admin', :pw, 'Administrador', True, True, NOW())
            """), {"pw": hashed})
            print("Admin user created with ID 3 and is_admin=True")
        else:
            # Update existing admin
            conn.execute(text("UPDATE users SET is_admin = True, hashed_password = :pw WHERE username = 'admin'"), {"pw": hashed})
            print("Admin user updated to is_admin=True")
            
        conn.commit()
            
except Exception as e:
    print(f"Error: {e}")
