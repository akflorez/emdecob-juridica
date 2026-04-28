
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.models import User

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
# Token proporcionado por el usuario anteriormente
TOKEN = "pk_26368479_4ISVQXGZFEQZZGYOA1IOV32BUIE41TGX"

async def run_migration():
    if not NEON_URL:
        print("Missing NEON_URL")
        return
    
    engine = create_engine(NEON_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Usuario 2 es jurico_emdecob en Neon
    print(f"Starting DIRECT migration to NEON production for User 2...")
    try:
        # Esto mapeará todo lo de Juan Jose Escobar al ID 2 (jurico_emdecob)
        await migrate_clickup_to_emdecob(TOKEN, db, 2)
        print("Migration to Neon finished successfully!")
    except Exception as e:
        print(f"Migration to Neon failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
