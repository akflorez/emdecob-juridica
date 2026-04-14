import sys
import os
import asyncio
sys.path.append(os.getcwd())

from backend.database import SessionLocal, Case
from backend.main import save_new_publications

async def main():
    db = SessionLocal()
    case = db.query(Case).filter(Case.demandado.like("%AUGUSTO PAVANI%")).first()
    if not case:
        print("Caso Augusto Pavani no encontrado")
        return
        
    print(f"Probando caso: {case.demandado} - {case.radicado}")
    # Simular lo que hace refresh-publicaciones
    await save_new_publications(case, db)
    db.commit()
    print("Sincronización terminada")

if __name__ == "__main__":
    asyncio.run(main())
