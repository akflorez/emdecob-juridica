import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def list_columns():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'cases';
        """)
        
        rows = cur.fetchall()
        print("--- Columnas en tabla 'cases' ---")
        for r in rows:
            print(f"{r['column_name']} ({r['data_type']})")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_columns()
