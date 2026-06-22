import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.db import engine

def main():
    print("="*60)
    print("APLICACIÓN MANUAL DE MIGRACIONES P0 (CONSTRAINTS)")
    print("="*60)
    
    dialect_name = engine.dialect.name
    if dialect_name != "postgresql":
        print("[ERROR] Este script está diseñado exclusivamente para PostgreSQL.")
        sys.exit(1)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a PostgreSQL: {e}")
        sys.exit(1)

    print("\n--- 1. DIAGNÓSTICO PREVIO ---")
    
    with engine.connect() as conn:
        # Check invalid_radicados NULLs
        ir_nulls = conn.execute(text("SELECT COUNT(*) FROM invalid_radicados WHERE company_id IS NULL")).scalar()
        print(f"invalid_radicados con company_id NULL: {ir_nulls}")
        
        # Check invalid_radicados duplicates
        ir_dups = conn.execute(text("""
            SELECT company_id, radicado, COUNT(*) as count
            FROM invalid_radicados
            GROUP BY company_id, radicado
            HAVING COUNT(*) > 1
        """)).all()
        print(f"Duplicados en invalid_radicados (company_id, radicado): {len(ir_dups)}")
        
        # Check publicaciones_busquedas NULLs
        pb_nulls = conn.execute(text("SELECT COUNT(*) FROM publicaciones_busquedas WHERE company_id IS NULL OR mes_busqueda IS NULL OR mes_busqueda = ''")).scalar()
        print(f"publicaciones_busquedas con company_id NULL o mes_busqueda inválido: {pb_nulls}")
        
        # Check publicaciones_busquedas duplicates
        pb_dups = conn.execute(text("""
            SELECT company_id, radicado, mes_busqueda, COUNT(*) as count
            FROM publicaciones_busquedas
            GROUP BY company_id, radicado, mes_busqueda
            HAVING COUNT(*) > 1
        """)).all()
        print(f"Duplicados en publicaciones_busquedas (company_id, radicado, mes_busqueda): {len(pb_dups)}")

        if ir_nulls > 0 or len(ir_dups) > 0 or pb_nulls > 0 or len(pb_dups) > 0:
            print("\n[ERROR] Hay inconsistencias en los datos. No se pueden aplicar las constraints UNIQUE.")
            print("Por favor resuelva los duplicados o registros NULL antes de continuar.")
    print("\n--- 1.5 CONSTRAINTS ACTUALES EN POSTGRESQL ---")
    try:
        with engine.connect() as conn:
            # Constraints en invalid_radicados
            c_ir = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'invalid_radicados'::regclass")).fetchall()
            print("Constraints en invalid_radicados:")
            for row in c_ir: print(f"  - {row[0]}")
            
            # Constraints en publicaciones_busquedas
            c_pb = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'publicaciones_busquedas'::regclass")).fetchall()
            print("Constraints en publicaciones_busquedas:")
            for row in c_pb: print(f"  - {row[0]}")
    except Exception as e:
        print(f"[ERROR] No se pudieron leer las constraints: {e}")

    print("\n--- 1.6 BACKUP LÓGICO DE TABLAS AFECTADAS ---")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_ir = f"backup_invalid_radicados_{ts}"
    backup_pb = f"backup_publicaciones_busquedas_{ts}"
    
    try:
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            print(f"Respaldando invalid_radicados en: {backup_ir}...")
            conn.execute(text(f"CREATE TABLE {backup_ir} AS SELECT * FROM invalid_radicados"))
            
            print(f"Respaldando publicaciones_busquedas en: {backup_pb}...")
            conn.execute(text(f"CREATE TABLE {backup_pb} AS SELECT * FROM publicaciones_busquedas"))
            
            print("[OK] Backups lógicos completados exitosamente.")
    except Exception as e:
        print(f"[ERROR CRÍTICO] Falló el backup de las tablas: {e}")
        print("MIGRACIÓN CANCELADA por seguridad. No se alterarán las constraints.")
        sys.exit(1)

    print("\n--- 2. APLICANDO CONSTRAINTS (CON TIMEOUTS) ---")
    
    # We use isolated autocommit connections to apply timeouts globally for the session
    try:
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
            print("Configurando lock_timeout = '5s' y statement_timeout = '60s'...")
            conn.execute(text("SET lock_timeout = '5s'"))
            conn.execute(text("SET statement_timeout = '60s'"))
            
            # --- invalid_radicados ---
            print("\nAplicando a invalid_radicados...")
            try:
                conn.execute(text("ALTER TABLE invalid_radicados DROP CONSTRAINT IF EXISTS invalid_radicados_radicado_key"))
                conn.execute(text("ALTER TABLE invalid_radicados DROP CONSTRAINT IF EXISTS uq_invalid_radicado_company"))
                conn.execute(text("ALTER TABLE invalid_radicados ADD CONSTRAINT uq_invalid_radicado_company UNIQUE (company_id, radicado)"))
                print("[OK] Constraint uq_invalid_radicado_company aplicada exitosamente.")
            except Exception as e:
                print(f"[ERROR] Falló al aplicar constraint a invalid_radicados: {e}")
                print("Se requiere ventana de mantenimiento o liberar locks activos.")
                sys.exit(1)

            # --- publicaciones_busquedas ---
            print("\nAplicando a publicaciones_busquedas...")
            try:
                conn.execute(text("ALTER TABLE publicaciones_busquedas DROP CONSTRAINT IF EXISTS uix_pub_search_radicado_mes"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas DROP CONSTRAINT IF EXISTS uix_pub_search_company_radicado_mes"))
                conn.execute(text("ALTER TABLE publicaciones_busquedas ADD CONSTRAINT uix_pub_search_company_radicado_mes UNIQUE (company_id, radicado, mes_busqueda)"))
                print("[OK] Constraint uix_pub_search_company_radicado_mes aplicada exitosamente.")
            except Exception as e:
                print(f"[ERROR] Falló al aplicar constraint a publicaciones_busquedas: {e}")
                print("Se requiere ventana de mantenimiento o liberar locks activos.")
                sys.exit(1)
                
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] Error en la conexión/sesión para aplicar constraints: {e}")
        sys.exit(1)

    print("\n" + "="*60)
    print("MIGRACIÓN APLICADA CON ÉXITO")
    print("El backend ahora puede trabajar de forma segura con las restricciones UNIQUE.")
    print("="*60)

if __name__ == "__main__":
    main()
