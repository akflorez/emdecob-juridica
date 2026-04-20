import asyncio
import sys
import os
import traceback

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from backend.clickup_sync import migrate_clickup_to_emdecob
from backend.db import SessionLocal

API_TOKEN = "pk_26368479_XJ7PY2A698WPBXVSB2P214EDLDTZKRJF"
ADMIN_USER_ID = 2 

async def run():
    print("Iniciando migracion manual de ClickUp (Verbose)...")
    db = SessionLocal()
    try:
        result = await migrate_clickup_to_emdecob(API_TOKEN, db, ADMIN_USER_ID)
        print(f"Resultado final: {result}")
    except Exception as e:
        print("--- ERROR DETECTADO ---")
        print(f"Tipo: {type(e)}")
        print(f"Mensaje: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run())
