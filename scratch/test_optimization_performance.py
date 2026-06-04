import os
import sys
import asyncio
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend.models import User, Case, CaseEvent
from backend.main import get_event_documents, get_task_detail, get_db

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class MockRequest:
    def __init__(self, headers):
        self.headers = headers

async def test_docs_performance():
    print("\n=== TESTING DOCUMENTS ENDPOINT PERFORMANCE ===")
    db = SessionLocal()
    try:
        # We will use id_reg_actuacion=3532787571 and radicado=70001400300620180045500
        id_reg = 3532787571
        radicado = "70001400300620180045500"
        
        # Clear cache first to test a "cold" call
        event = db.query(CaseEvent).filter(CaseEvent.id_reg_actuacion == id_reg).first()
        if event:
            event.documentos_cache = None
            db.commit()
            print("Cleared documentos_cache for testing.")
            
        # 1. Cold Call (without cache)
        print("\n[COLD CALL] Requesting documents (no cache, queries API)...")
        start = time.time()
        res_cold = await get_event_documents(id_reg_actuacion=id_reg, llave_proceso=radicado, db=db)
        duration_cold = time.time() - start
        print(f"Cold call completed in: {duration_cold:.3f} seconds | Found {len(res_cold.get('items', []))} documents.")
        
        # 2. Warm Call (with cache)
        print("\n[WARM CALL] Requesting documents (cached in DB)...")
        start = time.time()
        res_warm = await get_event_documents(id_reg_actuacion=id_reg, llave_proceso=radicado, db=db)
        duration_warm = time.time() - start
        print(f"Warm call completed in: {duration_warm:.6f} seconds | Found {len(res_warm.get('items', []))} documents.")
        
        # Print speedup
        speedup = duration_cold / duration_warm if duration_warm > 0 else float('inf')
        print(f"\n⚡ SPEEDUP FOR DOCUMENTS: {speedup:.1f}x faster!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

async def test_tasks_performance():
    print("\n=== TESTING TASK DETAIL ENDPOINT PERFORMANCE ===")
    db = SessionLocal()
    try:
        # Find any task with a ClickUp ID
        task = db.query(CaseEvent).filter(CaseEvent.id_reg_actuacion != None).first() # Just checking
        from backend.models import Task
        t = db.query(Task).filter(Task.clickup_id != None).first()
        if not t:
            print("No ClickUp tasks found in database to test.")
            return
            
        print(f"Testing with Task ID={t.id} | ClickUp ID={t.clickup_id} | Title={t.title}")
        
        # Reset updated_at to long ago to force sync on first call
        import datetime
        t.updated_at = datetime.datetime.now() - datetime.timedelta(days=1)
        db.commit()
        
        # Mock request with ClickUp token
        headers = {"X-ClickUp-Token": "pk_test_token_some_mock"}
        request = MockRequest(headers=headers)
        current_user = db.query(User).filter(User.is_admin == True).first()
        
        # 1. Cold Call (queries ClickUp API)
        # Note: Since the token is mock, it will fail/skip ClickUp fetch but we measure local db check vs ClickUp timeout/run time.
        print("\n[COLD CALL] Requesting task detail (freshness expired, attempts ClickUp fetch)...")
        start = time.time()
        # We catch exceptions since mock token fails ClickUp fetch
        try:
            await get_task_detail(task_id=t.id, request=request, db=db, current_user=current_user)
        except Exception:
            pass
        duration_cold = time.time() - start
        print(f"Cold call duration: {duration_cold:.3f} seconds.")
        
        # 2. Warm Call (within 2-minute freshness window, bypasses ClickUp fetch)
        print("\n[WARM CALL] Requesting task detail (fresh, served from DB directly)...")
        start = time.time()
        res_warm = await get_task_detail(task_id=t.id, request=request, db=db, current_user=current_user)
        duration_warm = time.time() - start
        print(f"Warm call completed in: {duration_warm:.6f} seconds.")
        
        # Print speedup
        speedup = duration_cold / duration_warm if duration_warm > 0 else float('inf')
        print(f"\n⚡ SPEEDUP FOR TASKS: {speedup:.1f}x faster!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

async def main():
    await test_docs_performance()
    await test_tasks_performance()

if __name__ == "__main__":
    asyncio.run(main())
