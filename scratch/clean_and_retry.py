import os
import sys

sys.path.append(os.getcwd())
from backend.db import SessionLocal
from backend.models import Case, CasePublication, CasePublicationSearch

def main():
    db = SessionLocal()
    try:
        rad = "11001400300720250052200"
        case = db.query(Case).filter(Case.radicado == rad).first()
        if not case:
            print(f"Case with radicado {rad} not found!")
            return
            
        # Delete publications with None dates or all publications for this case to start clean
        deleted_count = db.query(CasePublication).filter(CasePublication.case_id == case.id).delete()
        print(f"Deleted {deleted_count} publications for case {rad} from database.")
        
        # Reset search month statuses so they are not blocked by 'buscando'
        deleted_searches = db.query(CasePublicationSearch).filter(CasePublicationSearch.radicado == rad).delete()
        print(f"Deleted {deleted_searches} search logs for case {rad} from database.")
        
        db.commit()
        print("Database cleaned up successfully!")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
