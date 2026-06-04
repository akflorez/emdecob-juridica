import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking recent sync logs...")
        res = conn.execute(text("""
            SELECT l.id, l.case_id, c.radicado, l.message, l.created_at 
            FROM sync_debug_logs l
            JOIN cases c ON l.case_id = c.id
            ORDER BY l.id DESC 
            LIMIT 5
        """))
        recent_logs = res.fetchall()
        for r in recent_logs:
            print(f"  ID: {r[0]} | Radicado: {r[2]} | Msg: {r[3]} | Created At: {r[4]}")
            
except Exception as e:
    print(f"Error checking DB: {e}")
