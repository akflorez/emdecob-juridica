
from backend.db import SessionLocal
from backend.models import User, Case
from sqlalchemy import or_

def check():
    db = SessionLocal()
    try:
        usernames = ['jurico_emdecob', 'jurico.emdecob', 'juricob']
        users = db.query(User).filter(User.username.in_(usernames)).all()
        
        print(f"{'ID':<5} | {'Username':<20} | {'Total Cases':<12} | {'With Juzgado':<12}")
        print("-" * 55)
        
        for u in users:
            total = db.query(Case).filter(Case.user_id == u.id).count()
            with_juzgado = db.query(Case).filter(Case.user_id == u.id, Case.juzgado.isnot(None)).count()
            print(f"{u.id:<5} | {u.username:<20} | {total:<12} | {with_juzgado:<12}")
            
        # Check if there are cases with no user_id or different user_id that might belong to them
        # (e.g. if their name is in the 'abogado' field)
        print("\nChecking cases by 'abogado' field matching these users' names:")
        for u in users:
            if u.nombre:
                by_abogado = db.query(Case).filter(Case.abogado == u.nombre).count()
                by_abogado_no_uid = db.query(Case).filter(Case.abogado == u.nombre, Case.user_id.is_(None)).count()
                print(f"Name: {u.nombre} (User: {u.username}) -> Cases by 'abogado' field: {by_abogado} ({by_abogado_no_uid} with no user_id)")

    finally:
        db.close()

if __name__ == '__main__':
    check()
