import asyncio
from backend.db import SessionLocal
from backend.models import Case
from backend.service.rama import actuaciones_proceso

async def run():
    db = SessionLocal()
    try:
        case = db.query(Case).filter_by(id=409).first()
        if not case:
            print("Case not found")
            return
        print(f"Syncing case: {case.radicado}")
        acts = await actuaciones_proceso(case.id_proceso or case.radicado)
        print(f"Found {len(acts)} actuaciones")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(run())
