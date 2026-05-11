import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def check_sync_status():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Consultar casos que tienen progreso > 0 pero no han terminado
        cur.execute("""
            SELECT id, radicado, sync_pub_progress, sync_pub_status, updated_at 
            FROM cases 
            WHERE sync_pub_progress > 0 AND sync_pub_progress < 100
            ORDER BY updated_at DESC
            LIMIT 5;
        """)
        
        rows = cur.fetchall()
        print(f"--- Casos en proceso de sincronización ({len(rows)}) ---")
        for r in rows:
            print(f"ID: {r['id']} | Radicado: {r['radicado']} | Progreso: {r['sync_pub_progress']}% | Status: {r['sync_pub_status']} | Último update: {r['updated_at']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error conectando a la DB: {e}")

if __name__ == "__main__":
    check_sync_status()
