import asyncio
from backend.db import SessionLocal
from backend.main import get_case_publications
from backend.models import User

async def run():
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username='superadmin').first()
        res = await get_case_publications('11001400306720250052600', db, user)
        print("Success:", res.keys())
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(run())
