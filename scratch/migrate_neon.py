
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.models import User

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
TOKEN = "pk_26368479_4ISVQXGZFEQZZGYOA1IOV32BUIE41TGX"

async def run_migration():
    if not NEON_URL:
        print("Missing NEON_URL")
        return
    
    engine = create_engine(NEON_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Encontrar admin para ser el owner
    admin = db.query(User).filter(User.is_admin == True).first()
    if not admin:
        admin = db.query(User).first()
        
    print(f"Starting migration for Neon with owner {admin.username} (ID: {admin.id})")
    try:
        await migrate_clickup_to_emdecob(TOKEN, db, admin.id)
        print("Migration finished successfully on Neon!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
