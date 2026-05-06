
from backend.db import SessionLocal
from backend.models import Case, User

def check():
    db = SessionLocal()
    results = db.query(User.id, User.username, User.nombre).all()
    user_map = {u.id: u.username for u in results}
    
    counts = db.query(Case.user_id).group_by(Case.user_id).all()
    print("Case counts by User ID:")
    for (uid,) in counts:
        c_count = db.query(Case).filter(Case.user_id == uid).count()
        uname = user_map.get(uid, "Unknown")
        print(f"User ID: {uid}, Username: {uname}, Count: {c_count}")
    
    db.close()

if __name__ == "__main__":
    check()
