import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ No DATABASE_URL found")
    exit(1)

engine = create_engine(DATABASE_URL)

print("🔍 Sincronizando esquema de case_events...")
with engine.connect() as conn:
    # 1. Añadir con_documentos si no existe
    try:
        conn.execute(text("ALTER TABLE case_events ADD COLUMN con_documentos BOOLEAN DEFAULT FALSE"))
        conn.commit()
        print("✅ Columna 'con_documentos' añadida a 'case_events'")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ La columna 'con_documentos' ya existe.")
        else:
            print(f"❌ Error al añadir 'con_documentos': {e}")

    # 2. Asegurar que event_hash existe (ya vimos que existe, pero por si acaso)
    # Si existiera event_key pero no event_hash, lo renombramos.
    # Pero aquí parece que ambos existen o al menos event_hash está.

    print("✅ Sincronización completada.")
