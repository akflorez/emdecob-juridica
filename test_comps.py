import asyncio
from backend.main import get_admin_companies
from backend.db import SessionLocal
from backend.models import User, Company
from sqlalchemy import text

db = SessionLocal()

# Add missing columns manually for testing locally
try:
    with db.begin_nested():
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspension_reason TEXT;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS suspended_by INTEGER;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS reactivated_at TIMESTAMP;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS reactivated_by INTEGER;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'al_dia';"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS next_payment_due DATE;"))
        db.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS billing_notes TEXT;"))
    db.commit()
except Exception as e:
    db.rollback()
    print("MIGRATE ERROR:", e)

superadmin = db.query(User).filter(User.is_admin == True, User.company_id == None).first()

async def test():
    try:
        comps = await get_admin_companies(db=db, current_user=superadmin)
        print("COMPS RETURNED:", type(comps), comps)
        # Try to serialize them using fastapi jsonable_encoder
        from fastapi.encoders import jsonable_encoder
        encoded = jsonable_encoder(comps)
        print("ENCODED SUCCESS:", len(encoded))
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test())
