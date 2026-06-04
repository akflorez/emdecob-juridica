import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Checking active cases sync status...")
        res = conn.execute(text("""
            SELECT id, radicado, sync_pub_progress, sync_pub_status, updated_at 
            FROM cases 
            WHERE sync_pub_progress > 0 OR sync_pub_status IS NOT NULL
        """))
        active_cases = res.fetchall()
        print(f"Cases with active sync progress/status: {len(active_cases)}")
        for r in active_cases:
            print(f"  ID: {r[0]} | Radicado: {r[1]} | Progress: {r[2]} | Status: {r[3]} | Updated At: {r[4]}")
            
except Exception as e:
    print(f"Error checking DB: {e}")
