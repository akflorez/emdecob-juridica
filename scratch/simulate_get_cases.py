
from backend.db import SessionLocal
from backend.models import User, Case
from sqlalchemy import or_, and_, desc
from datetime import datetime, date, timedelta
import pytz

TIMEZONE_CO = pytz.timezone("America/Bogota")
def today_colombia():
    return datetime.now(TIMEZONE_CO).date()

def check():
    db = SessionLocal()
    current_user = db.query(User).filter(User.id == 2).first()
    
    # Simulate list_cases
    solo_validos = True
    solo_pendientes = False
    
    q = db.query(Case)
    is_jurico = "juri" in current_user.username.lower() or current_user.id == 2
    
    if is_jurico:
        q = q.filter(Case.user_id == current_user.id)
    
    if solo_pendientes:
        q = q.filter(Case.juzgado.is_(None))
    elif solo_validos:
        q = q.filter(Case.juzgado.isnot(None))

    total = q.count()
    items = q.order_by(desc(Case.ultima_actuacion)).limit(20).all()

    print(f"List Cases for {current_user.username} (ID: {current_user.id}):")
    print(f"  Total: {total}")
    print(f"  Items returned: {len(items)}")
    for c in items:
        print(f"    - {c.radicado} (Juzgado: {c.juzgado})")

    db.close()

if __name__ == "__main__":
    check()
