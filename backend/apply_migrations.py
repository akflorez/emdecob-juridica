import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add parent directory to path to import db and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import engine, Base
from backend.models import Case, CaseEvent, InvalidRadicado, User, CasePublication, SearchJob

def run_migrations():
    print("🚀 Iniciando migración de base de datos...")
    
    # 1. Crear tablas nuevas si no existen
    print("📋 Creando tablas nuevas (si faltan)...")
    Base.metadata.create_all(bind=engine)
    
    # 2. Agregar columnas faltantes a la tabla 'cases'
    print("🔧 Verificando columnas en la tabla 'cases'...")
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('cases')]
    
    with engine.begin() as conn:
        if 'cedula' not in columns:
            print("➕ Agregando columna 'cedula' a 'cases'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN cedula VARCHAR(50)"))
        
        if 'abogado' not in columns:
            print("➕ Agregando columna 'abogado' a 'cases'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN abogado VARCHAR(200)"))
            
        if 'id_proceso' not in columns:
            print("➕ Agregando columna 'id_proceso' a 'cases'...")
            conn.execute(text("ALTER TABLE cases ADD COLUMN id_proceso VARCHAR(20)"))
            conn.execute(text("CREATE UNIQUE INDEX ix_cases_id_proceso ON cases (id_proceso)"))

    print("✅ Migración completada con éxito!")

if __name__ == "__main__":
    run_migrations()
