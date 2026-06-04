import sys
from sqlalchemy import create_engine, text
from backend.db import Base, engine, SessionLocal
from backend.models import User, Company

def main():
    print("Iniciando migración completa de SaaS (Multi-empresa)...")
    
    # 1. Agregar las columnas si no existen (SQL puro para SQLite/Postgres)
    tables_to_add = [
        "case_events", 
        "case_publications", 
        "tasks", 
        "search_jobs", 
        "workspaces", 
        "invalid_radicados"
    ]
    
    with engine.begin() as conn:
        for t in tables_to_add:
            try:
                print(f"Agregando company_id a {t}...")
                conn.execute(text(f"ALTER TABLE {t} ADD COLUMN company_id INTEGER"))
                conn.execute(text(f"CREATE INDEX ix_{t}_company_id ON {t} (company_id)"))
            except Exception as e:
                # La columna ya existe o error en BD (seguramente ya existe si corremos 2 veces)
                print(f"Nota en {t}: {str(e).split()[0]} (posiblemente ya existe)")

    # 2. Lógica de mapeo en sesión
    db = SessionLocal()
    try:
        # A. Crear empresa CODE si no existe
        code_company = db.query(Company).filter(Company.nombre == "CODE").first()
        if not code_company:
            # Reutilizar la 1 si existe
            code_company = db.query(Company).filter(Company.id == 1).first()
            if code_company:
                code_company.nombre = "CODE"
            else:
                code_company = Company(id=1, nombre="CODE", estado="activo")
                db.add(code_company)
            db.commit()
            db.refresh(code_company)
            
        print(f"Empresa CODE identificada con ID: {code_company.id}")

        # B. Actualizar usuarios (Superadmin queda NULL)
        db.execute(text(f"UPDATE users SET company_id = {code_company.id} WHERE company_id IS NULL AND username != 'superadmin'"))
        
        # C. Actualizar resto de tablas
        tables_to_update = [
            "cases",
            "case_events",
            "case_publications",
            "publicaciones_busquedas",
            "tasks",
            "search_jobs",
            "workspaces",
            "invalid_radicados",
            "audit_logs"
        ]
        
        for t in tables_to_update:
            try:
                res = db.execute(text(f"UPDATE {t} SET company_id = {code_company.id} WHERE company_id IS NULL"))
                print(f"Actualizados {res.rowcount} registros en {t}.")
            except Exception as e:
                print(f"Error actualizando {t}: {e}")
                
        db.commit()
        print("Migración completada exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"Error crítico en la migración: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
