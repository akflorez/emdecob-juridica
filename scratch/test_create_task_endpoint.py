import os
import sys
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend.models import User, Case, Task
from backend.main import create_task, TaskCreate, get_db

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

async def test_endpoint():
    db = SessionLocal()
    try:
        # Get admin user as current_user
        current_user = db.query(User).filter(User.is_admin == True).first()
        if not current_user:
            print("No admin user found")
            return
            
        print(f"Using admin user: ID={current_user.id}, Username={current_user.username}")
        
        # We will try to create a task for case 1470 with invalid list_id=1
        t_data = TaskCreate(
            title="TEST GESTION ROBUS_DB",
            description="Created by automated endpoint verification",
            list_id=1,  # Invalid list ID
            status="TO DO",
            priority="normal",
            case_id=1470,
            parent_id=None
        )
        
        print("\nInvoking create_task endpoint with list_id=1...")
        task_created = await create_task(t_data=t_data, db=db, current_user=current_user)
        print(f"Task created successfully!")
        print(f"  ID: {task_created.id}")
        print(f"  Title: {task_created.title}")
        print(f"  Resolved list_id: {task_created.list_id}")
        print(f"  Case ID: {task_created.case_id}")
        
        # Clean up test task
        print("\nCleaning up test task...")
        db.delete(task_created)
        db.commit()
        print("Test task deleted. DB is clean!")
        
    except Exception as e:
        db.rollback()
        print(f"Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
