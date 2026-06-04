import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from backend.models import Task, User, ProjectList

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def main():
    db = SessionLocal()
    try:
        print("Simulating task creation with list_id=1...")
        task = Task(
            title="dddd",
            description="Gestión para Radicado: 70001400300620180045500",
            list_id=1,  # Invalid list ID
            status="TO DO",
            priority="normal",
            case_id=1470,
            creator_id=3  # Admin ID
        )
        db.add(task)
        db.commit()
        print("Success! (Should not happen if list_id 1 is invalid)")
    except Exception as e:
        db.rollback()
        print(f"Error caught as expected: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
