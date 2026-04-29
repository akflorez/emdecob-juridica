
import sqlalchemy
from sqlalchemy import create_engine, inspect

SERVER_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

try:
    engine = create_engine(SERVER_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in DB: {tables}")
    
    if "cases" in tables:
        with engine.connect() as conn:
            from sqlalchemy import text
            count = conn.execute(text("SELECT COUNT(*) FROM cases")).scalar()
            print(f"Total cases: {count}")
            
            sample = conn.execute(text("SELECT id, radicado, demandado FROM cases LIMIT 5")).fetchall()
            print("Sample cases:")
            for s in sample:
                print(f"- ID: {s[0]} | Radicado: {s[1]} | Demandado: {s[2]}")
            
except Exception as e:
    print(f"Error: {e}")
