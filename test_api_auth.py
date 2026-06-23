import os
import asyncio
from backend.main import get_admin_companies, get_billing_tiers
from backend.db import SessionLocal
from backend.models import User

db = SessionLocal()
superadmin = db.query(User).filter(User.is_admin == True, User.company_id == None).first()

if not superadmin:
    superadmin = User(username="test_superadmin", email="test@test.com", is_admin=True, hashed_password="x")
    db.add(superadmin)
    db.commit()
    db.refresh(superadmin)

async def test():
    print("Testing get_admin_companies...")
    try:
        comps = await get_admin_companies(db=db, current_user=superadmin)
        print("Comps length:", len(comps))
    except Exception as e:
        print("ERROR IN COMPANIES:", e)
        
    print("Testing get_billing_tiers...")
    try:
        tiers = await get_billing_tiers(db=db, current_user=superadmin)
        print("Tiers length:", len(tiers.get('tiers', [])))
    except Exception as e:
        print("ERROR IN TIERS:", e)

asyncio.run(test())
