
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.models import User, Base

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")
TOKEN = "pk_26368479_4ISVQXGZFEQZZGYOA1IOV32BUIE41TGX"

async def run():
    # 1. Copiar usuario de local a Neon
    e_local = create_engine(LOCAL_DB)
    S_local = sessionmaker(bind=e_local)
    db_local = S_local()
    users = db_local.query(User).all()

    e_prod = create_engine(NEON_URL)
    S_prod = sessionmaker(bind=e_prod)
    db_prod = S_prod()

    for u in users:
        existing = db_prod.query(User).filter(User.id == u.id).first()
        if not existing:
            print(f"Copying user {u.username} to Neon")
            new_u = User(
                id=u.id, 
                username=u.username, 
                hashed_password=u.hashed_password, 
                is_admin=u.is_admin,
                nombre=u.nombre
            )
            db_prod.add(new_u)
    db_prod.commit()

    # 2. Correr ClickUp Sync en Neon para User 2
    print("Starting ClickUp Sync to Neon...")
    try:
        await migrate_clickup_to_emdecob(TOKEN, db_prod, 2)
        print("Neon Sync complete!")
    except Exception as e:
        print(f"Neon Sync error: {e}")
    finally:
        db_prod.close()
        db_local.close()

if __name__ == "__main__":
    asyncio.run(run())
