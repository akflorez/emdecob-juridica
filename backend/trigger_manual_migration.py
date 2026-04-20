import asyncio
import sys
import os

# Añadir el directorio actual al path para evitar ModuleNotFoundError
sys.path.append(os.getcwd())

from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.db import SessionLocal

API_TOKEN = "pk_26368479_XJ7PY2A698WPBXVSB2P214EDLDTZKRJF"
ADMIN_USER_ID = 2  # Usamos el ID del admin (Santiago/Paul)

async def run():
    print("Iniciando migración manual de ClickUp...")
    db = SessionLocal()
    try:
        result = await migrate_clickup_to_emdecob(API_TOKEN, db, ADMIN_USER_ID)
        print(f"Resultado final: {result}")
    except Exception as e:
        print(f"Error durante la migración: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run())
