import os
import sys
import asyncio
import time
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend.models import User, Task
from backend.main import get_task_detail, get_db, now_colombia

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class MockRequest:
    def __init__(self, headers):
        self.headers = headers

async def test_fresh_task():
    db = SessionLocal()
    try:
        # Find any ClickUp task
        t = db.query(Task).filter(Task.clickup_id != None).first()
        if not t:
            print("No ClickUp task found.")
            return
            
        print(f"Testing fresh task bypass for ID={t.id}")
        
        # Manually mark as fresh (updated_at = now)
        t.updated_at = now_colombia()
        db.commit()
        
        # Verify age_seconds
        age = (now_colombia() - t.updated_at).total_seconds()
        print(f"Set updated_at. Current age: {age:.3f} seconds (should be < 120)")
        
        headers = {"X-ClickUp-Token": "pk_test_token_some_mock"}
        request = MockRequest(headers=headers)
        current_user = db.query(User).filter(User.is_admin == True).first()
        
        # Request task detail
        print("Requesting task detail (fresh)...")
        start = time.time()
        res = await get_task_detail(task_id=t.id, request=request, db=db, current_user=current_user)
        duration = time.time() - start
        
        print(f"Request completed in: {duration:.6f} seconds.")
        if duration < 0.05:
            print("SUCCESS: Endpoint bypassed ClickUp sync and returned instantly!")
        else:
            print("FAILURE: Endpoint did not bypass ClickUp sync.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_fresh_task())
