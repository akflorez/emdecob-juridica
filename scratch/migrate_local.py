
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.models import User

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
TOKEN = "pk_26368479_4ISVQXGZFEQZZGYOA1IOV32BUIE41TGX"

async def run_migration():
    if not DB_URL:
        print("Missing DATABASE_URL")
        return
    
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Usuario 2 es Juridico
    juridico = db.query(User).filter(User.id == 2).first()
    if not juridico:
        juridico = db.query(User).filter(User.username.ilike('%juri%')).first()
        
    print(f"Starting migration for LOCAL DB with user {juridico.username} (ID: {juridico.id})")
    try:
        # Usamos juridico como owner para que herede todo si no hay mapeo, 
        # pero mi logica en clickup_sync ya forza a 'juan jose escobar' -> ID de juridico.
        await migrate_clickup_to_emdecob(TOKEN, db, juridico.id)
        print("Migration finished successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
