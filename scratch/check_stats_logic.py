
from backend.db import SessionLocal
from backend.models import User, Case, InvalidRadicado
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import pytz

TIMEZONE_CO = pytz.timezone("America/Bogota")
def today_colombia():
    return datetime.now(TIMEZONE_CO).date()

def check():
    db = SessionLocal()
    current_user = db.query(User).filter(User.id == 2).first()
    
    q_validos = db.query(Case).filter(Case.juzgado.isnot(None))
    q_invalidos = db.query(InvalidRadicado)
    q_pendientes = db.query(Case).filter(Case.juzgado.is_(None))

    is_jurico = "juri" in current_user.username.lower() or current_user.id == 2
    
    if is_jurico:
        q_validos = q_validos.filter(Case.user_id == current_user.id)
        q_invalidos = q_invalidos.filter(InvalidRadicado.user_id == current_user.id)
        q_pendientes = q_pendientes.filter(Case.user_id == current_user.id)

    total_validos = q_validos.count()
    total_invalidos = q_invalidos.count()
    total_pendientes = q_pendientes.count()

    hoy = today_colombia()
    ayer = hoy - timedelta(days=1)

    q_no_leidos = db.query(Case).filter(
        Case.juzgado.isnot(None),
        Case.current_hash.isnot(None),
        or_(
            and_(Case.last_hash.isnot(None), Case.current_hash != Case.last_hash),
            and_(Case.last_hash.is_(None), Case.ultima_actuacion >= ayer),
        )
    )

    if is_jurico:
        q_no_leidos = q_no_leidos.filter(Case.user_id == current_user.id)

    print(f"Stats for {current_user.username} (ID: {current_user.id}):")
    print(f"  Valid: {total_validos}")
    print(f"  Pending: {total_pendientes}")
    print(f"  Invalid: {total_invalidos}")
    print(f"  No Leidos: {q_no_leidos.count()}")

    db.close()

if __name__ == "__main__":
    check()
