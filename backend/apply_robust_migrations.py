import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add parent directory to path to import db and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import engine, Base
from backend.models import Case, CaseEvent, InvalidRadicado, User, CasePublication, SearchJob

def run_migrations():
    print("[MIGRATION] Iniciando sincronizacion de esquema robusto...")
    
    # 1. Crear tablas nuevas si no existen (como CasePublication y SearchJob)
    print("[MIGRATION] Asegurando existencia de tablas...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Verificación de columnas usando Inspector
    inspector = inspect(engine)
    
    # --- Tabla 'cases' ---
    columns_cases = [c['name'] for c in inspector.get_columns('cases')]
    with engine.begin() as conn:
        if 'cedula' not in columns_cases:
            print("➕ [MIGRATION] cases: agregando 'cedula'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN cedula VARCHAR(50)"))
        
        if 'abogado' not in columns_cases:
            print("➕ [MIGRATION] cases: agregando 'abogado'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN abogado VARCHAR(200)"))
            
        if 'id_proceso' not in columns_cases:
            print("➕ [MIGRATION] cases: agregando 'id_proceso'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN id_proceso VARCHAR(20)"))
            try:
                conn.execute(text("CREATE UNIQUE INDEX ix_cases_id_proceso ON cases (id_proceso)"))
            except:
                pass
        
        if 'user_id' not in columns_cases:
            print("[MIGRATION] cases: agregando 'user_id'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN user_id INTEGER"))
            try:
                conn.execute(text("ALTER TABLE cases ADD CONSTRAINT fk_cases_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"))
            except:
                pass

    # --- Tabla 'case_events' ---
    columns_events = [c['name'] for c in inspector.get_columns('case_events')]
    with engine.begin() as conn:
        if 'con_documentos' not in columns_events:
            print("[MIGRATION] case_events: agregando 'con_documentos'...")
            # Usamos una sintaxis compatible con MySQL y Postgres
            conn.execute(text("ALTER TABLE case_events ADD COLUMN con_documentos BOOLEAN DEFAULT FALSE"))

    # --- Tabla 'invalid_radicados' ---
    columns_invalid = [c['name'] for c in inspector.get_columns('invalid_radicados')]
    with engine.begin() as conn:
        if 'user_id' not in columns_invalid:
            print("[MIGRATION] invalid_radicados: agregando 'user_id'...")
            conn.execute(text("ALTER TABLE invalid_radicados ADD COLUMN user_id INTEGER"))
            try:
                conn.execute(text("ALTER TABLE invalid_radicados ADD CONSTRAINT fk_invalid_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"))
            except:
                pass

    print("[MIGRATION] Sincronizacion finalizada satisfactoriamente.")

if __name__ == "__main__":
    run_migrations()
