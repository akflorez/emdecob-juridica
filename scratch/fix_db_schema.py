import psycopg2

DATABASE_URL = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob"

def run_migrations():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Añadiendo columnas a 'cases'...")
        cur.execute("ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_status VARCHAR(100);")
        cur.execute("ALTER TABLE cases ADD COLUMN IF NOT EXISTS sync_pub_progress INTEGER DEFAULT 0;")
        
        print("Añadiendo columnas a 'case_events'...")
        cur.execute("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS id_reg_actuacion BIGINT;")
        cur.execute("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS cons_actuacion BIGINT;")
        cur.execute("ALTER TABLE case_events ADD COLUMN IF NOT EXISTS documentos_cache TEXT;")
        
        print("Añadiendo índices...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_case_pub_case_id ON case_publications(case_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_case_event_case_id ON case_events(case_id);")
        
        conn.commit()
        print("¡Migraciones completadas exitosamente!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_migrations()
