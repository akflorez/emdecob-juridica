from backend.db import SessionLocal
from backend.main import list_cases
from backend.models import User
import asyncio

async def test():
    db=SessionLocal()
    u=db.query(User).filter(User.username=='jurico_emdecob').first()
    res=await list_cases(solo_pendientes=True, current_user=u, db=db, page=1, page_size=10)
    print(f'Pendientes found: {res["total"]}')
    db.close()
asyncio.run(test())
