
import sqlalchemy
from sqlalchemy import create_engine, text

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    with engine.connect() as conn:
        radicado = "11001418909420260125200"
        res = conn.execute(text("SELECT radicado FROM cases WHERE radicado LIKE :r"), {"r": f"%{radicado}%"}).fetchall()
        for r in res:
            print(f"Case radicado: {repr(r[0])}")
            
        res = conn.execute(text("SELECT title FROM tasks WHERE title LIKE :r"), {"r": f"%{radicado}%"}).fetchall()
        for r in res:
            print(f"Task title: {repr(r[0])}")
except Exception as e:
    print(f"Error: {e}")
