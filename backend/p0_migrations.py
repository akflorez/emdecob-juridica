import os
from datetime import datetime
from sqlalchemy import text, inspect
from backend.db import engine, SessionLocal

def run_p0_migrations():
    dialect_name = engine.dialect.name
    print(f"[P0-MIGRATION] Motor de base de datos detectado: {dialect_name}")
    
    # 1. Asegurar la existencia de la tabla excel_import_jobs
    with engine.begin() as conn:
        if dialect_name == "postgresql":
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS excel_import_jobs (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER,
                    usuario_username VARCHAR(255),
                    estado VARCHAR(50) DEFAULT 'pendiente',
                    total_filas INTEGER DEFAULT 0,
                    filas_procesadas INTEGER DEFAULT 0,
                    filas_creadas INTEGER DEFAULT 0,
                    filas_actualizadas INTEGER DEFAULT 0,
                    errores_parciales TEXT,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("[P0-MIGRATION] Tabla excel_import_jobs verificada/creada en PostgreSQL.")
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS excel_import_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    usuario_username VARCHAR(255),
                    estado VARCHAR(50) DEFAULT 'pendiente',
                    total_filas INTEGER DEFAULT 0,
                    filas_procesadas INTEGER DEFAULT 0,
                    filas_creadas INTEGER DEFAULT 0,
                    filas_actualizadas INTEGER DEFAULT 0,
                    errores_parciales TEXT,
                    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_fin TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("[P0-MIGRATION] Tabla excel_import_jobs verificada/creada en SQLite.")

    # 2. Diagnóstico y saneamiento de datos
    with SessionLocal() as db:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # --- DIAGNÓSTICO EN POSTGRESQL ---
        if dialect_name == "postgresql":
            # Listar restricciones de invalid_radicados
            if "invalid_radicados" in tables:
                constraints = db.execute(text("""
                    SELECT conname, contype 
                    FROM pg_constraint 
                    WHERE conrelid = 'invalid_radicados'::regclass;
                """)).all()
                print(f"[P0-MIGRATION] Restricciones actuales en invalid_radicados: {constraints}")
            
            # Listar restricciones de publicaciones_busquedas
            if "publicaciones_busquedas" in tables:
                constraints_pub = db.execute(text("""
                    SELECT conname, contype 
                    FROM pg_constraint 
                    WHERE conrelid = 'publicaciones_busquedas'::regclass;
                """)).all()
                print(f"[P0-MIGRATION] Restricciones actuales en publicaciones_busquedas: {constraints_pub}")

        # --- VERIFICACIÓN DE COMPANY_ID NULL ---
        # invalid_radicados
        if "invalid_radicados" in tables:
            null_count_ir = db.execute(text("SELECT COUNT(*) FROM invalid_radicados WHERE company_id IS NULL")).scalar()
            if null_count_ir > 0:
                rows_ir = db.execute(text("SELECT id, radicado, created_at, user_id FROM invalid_radicados WHERE company_id IS NULL")).all()
                print(f"[P0-MIGRATION][WARNING] Encontrados {null_count_ir} registros con company_id NULL en invalid_radicados:")
                for r in rows_ir:
                    print(f"  ID: {r[0]}, Radicado: {r[1]}, Creado: {r[2]}, Usuario: {r[3]}")
                # Detener y reportar si no hay forma de asignarlo de forma segura
                raise RuntimeError(f"MIGRATION BLOCK: Encontrados {null_count_ir} registros huérfanos (company_id NULL) en invalid_radicados. Deteniendo migración.")

        # publicaciones_busquedas
        if "publicaciones_busquedas" in tables:
            null_count_pb = db.execute(text("SELECT COUNT(*) FROM publicaciones_busquedas WHERE company_id IS NULL")).scalar()
            if null_count_pb > 0:
                rows_pb = db.execute(text("SELECT id, radicado, created_at, mes_busqueda FROM publicaciones_busquedas WHERE company_id IS NULL")).all()
                print(f"[P0-MIGRATION][WARNING] Encontrados {null_count_pb} registros con company_id NULL en publicaciones_busquedas:")
                for r in rows_pb:
                    print(f"  ID: {r[0]}, Radicado: {r[1]}, Creado: {r[2]}, Mes: {r[3]}")
                raise RuntimeError(f"MIGRATION BLOCK: Encontrados {null_count_pb} registros huérfanos (company_id NULL) en publicaciones_busquedas. Deteniendo migración.")

            # Limpiar registros con mes_busqueda NULL o vacío
            corrupt_count = db.execute(text("SELECT COUNT(*) FROM publicaciones_busquedas WHERE mes_busqueda IS NULL OR mes_busqueda = ''")).scalar()
            if corrupt_count > 0:
                print(f"[P0-MIGRATION] Detectados {corrupt_count} registros con mes_busqueda NULL o vacío. Eliminando registros corruptos...")
                # Backup primero
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_table = f"backup_corrupt_pub_search_{ts}"
                if dialect_name == "postgresql":
                    db.execute(text(f"CREATE TABLE {backup_table} AS SELECT * FROM publicaciones_busquedas WHERE mes_busqueda IS NULL OR mes_busqueda = ''"))
                else:
                    db.execute(text(f"CREATE TABLE {backup_table} AS SELECT * FROM publicaciones_busquedas WHERE mes_busqueda IS NULL OR mes_busqueda = ''"))
                
                db.execute(text("DELETE FROM publicaciones_busquedas WHERE mes_busqueda IS NULL OR mes_busqueda = ''"))
                db.commit()
                print(f"[P0-MIGRATION] Registros corruptos eliminados y respaldados en la tabla '{backup_table}'.")

        # --- VERIFICACIÓN DE DUPLICADOS Y RESPALDOS ---
        ts_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # invalid_radicados duplicados
        if "invalid_radicados" in tables:
            dup_query = """
                SELECT company_id, radicado, COUNT(*) as count 
                FROM invalid_radicados 
                GROUP BY company_id, radicado 
                HAVING COUNT(*) > 1
            """
            duplicates = db.execute(text(dup_query)).all()
            if duplicates:
                print(f"[P0-MIGRATION] Duplicados detectados en invalid_radicados: {duplicates}")
                # Encontrar ids de registros duplicados a eliminar (manteniendo el de mayor ID)
                ids_to_delete = []
                for company_id, radicado, count in duplicates:
                    rows = db.execute(text("""
                        SELECT id FROM invalid_radicados 
                        WHERE company_id = :comp_id AND radicado = :rad 
                        ORDER BY id DESC
                    """), {"comp_id": company_id, "rad": radicado}).all()
                    
                    # Conservamos el primero (mayor ID) y añadimos el resto a borrar
                    for row in rows[1:]:
                        ids_to_delete.append(row[0])
                
                if ids_to_delete:
                    backup_ir = f"backup_deleted_invalid_radicados_{ts_suffix}"
                    print(f"[P0-MIGRATION] Respaldando {len(ids_to_delete)} duplicados de invalid_radicados en tabla '{backup_ir}'...")
                    
                    # Crear tabla de respaldo e insertar filas
                    db.execute(text(f"CREATE TABLE {backup_ir} AS SELECT * FROM invalid_radicados WHERE id IN :ids"), {"ids": tuple(ids_to_delete)})
                    db.execute(text("DELETE FROM invalid_radicados WHERE id IN :ids"), {"ids": tuple(ids_to_delete)})
                    db.commit()
                    print("[P0-MIGRATION] Limpieza de duplicados completada.")

        # publicaciones_busquedas duplicados
        if "publicaciones_busquedas" in tables:
            dup_query_pb = """
                SELECT company_id, radicado, mes_busqueda, COUNT(*) as count 
                FROM publicaciones_busquedas 
                GROUP BY company_id, radicado, mes_busqueda 
                HAVING COUNT(*) > 1
            """
            duplicates_pb = db.execute(text(dup_query_pb)).all()
            if duplicates_pb:
                print(f"[P0-MIGRATION] Duplicados detectados en publicaciones_busquedas: {duplicates_pb}")
                ids_to_delete_pb = []
                for company_id, radicado, mes_busqueda, count in duplicates_pb:
                    rows = db.execute(text("""
                        SELECT id FROM publicaciones_busquedas 
                        WHERE company_id = :comp_id AND radicado = :rad AND mes_busqueda = :mes 
                        ORDER BY id DESC
                    """), {"comp_id": company_id, "rad": radicado, "mes": mes_busqueda}).all()
                    
                    for row in rows[1:]:
                        ids_to_delete_pb.append(row[0])
                
                if ids_to_delete_pb:
                    backup_pb = f"backup_deleted_publicaciones_busquedas_{ts_suffix}"
                    print(f"[P0-MIGRATION] Respaldando {len(ids_to_delete_pb)} duplicados de publicaciones_busquedas en tabla '{backup_pb}'...")
                    
                    db.execute(text(f"CREATE TABLE {backup_pb} AS SELECT * FROM publicaciones_busquedas WHERE id IN :ids"), {"ids": tuple(ids_to_delete_pb)})
                    db.execute(text("DELETE FROM publicaciones_busquedas WHERE id IN :ids"), {"ids": tuple(ids_to_delete_pb)})
                    db.commit()
                    print("[P0-MIGRATION] Limpieza de duplicados de publicaciones_busquedas completada.")

        # --- APLICAR CONSTRAINTS / ÍNDICES DE UNICIDAD ---
        if dialect_name == "postgresql":
            with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
                print("[P0-MIGRATION] Actualizando restricciones únicas en PostgreSQL...")
                try:
                    conn.execute(text("ALTER TABLE invalid_radicados DROP CONSTRAINT IF EXISTS invalid_radicados_radicado_key"))
                    conn.execute(text("ALTER TABLE invalid_radicados DROP CONSTRAINT IF EXISTS uq_invalid_radicado_company"))
                    conn.execute(text("ALTER TABLE invalid_radicados ADD CONSTRAINT uq_invalid_radicado_company UNIQUE (company_id, radicado)"))
                    print("[P0-MIGRATION] Constraint uq_invalid_radicado_company (company_id, radicado) aplicada con éxito.")
                except Exception as e:
                    print(f"[P0-MIGRATION] Error aplicando constraint unique a invalid_radicados: {e}")
                
                try:
                    conn.execute(text("ALTER TABLE publicaciones_busquedas DROP CONSTRAINT IF EXISTS uix_pub_search_radicado_mes"))
                    conn.execute(text("ALTER TABLE publicaciones_busquedas DROP CONSTRAINT IF EXISTS uix_pub_search_company_radicado_mes"))
                    conn.execute(text("ALTER TABLE publicaciones_busquedas ADD CONSTRAINT uix_pub_search_company_radicado_mes UNIQUE (company_id, radicado, mes_busqueda)"))
                    print("[P0-MIGRATION] Constraint uix_pub_search_company_radicado_mes aplicada con éxito.")
                except Exception as e:
                    print(f"[P0-MIGRATION] Error aplicando constraint unique a publicaciones_busquedas: {e}")
        else:
            # SQLite: Crear índices únicos para emular la restricción de unicidad
            with engine.connect() as conn:
                print("[P0-MIGRATION] Creando índices de unicidad en SQLite...")
                try:
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_invalid_radicado_company ON invalid_radicados (company_id, radicado)"))
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uix_pub_search_company_radicado_mes ON publicaciones_busquedas (company_id, radicado, mes_busqueda)"))
                    conn.commit()
                    print("[P0-MIGRATION] Índices de unicidad aplicados en SQLite.")
                except Exception as e:
                    print(f"[P0-MIGRATION] Error en índices de unicidad SQLite: {e}")

        # --- CREACIÓN DE ÍNDICES DE RENDIMIENTO (SOLO COLUMNAS EXISTENTES) ---
        print("[P0-MIGRATION] Creando índices de rendimiento si las columnas existen...")
        
        index_defs = [
            ("cases", "idx_cases_company_radicado", ["company_id", "radicado"]),
            ("cases", "idx_cases_company_created_at_desc", ["company_id", "created_at DESC"]),
            ("case_events", "idx_case_events_case_id_event_date_desc", ["case_id", "event_date DESC"]),
            ("case_publications", "idx_case_pubs_case_id_fecha_desc", ["case_id", "fecha_publicacion DESC"]),
            ("publicaciones_busquedas", "idx_pub_search_comp_rad_mes", ["company_id", "radicado", "mes_busqueda"]),
            ("publicaciones_busquedas", "idx_pub_search_estado", ["estado"]),
            ("publicaciones_busquedas", "idx_pub_search_company_estado", ["company_id", "estado"]),
            ("tasks", "idx_tasks_company_case", ["company_id", "case_id"]),
            ("users", "idx_users_company", ["company_id"])
        ]
        
        for table_name, index_name, columns in index_defs:
            if table_name in tables:
                cols_info = [c['name'] for c in inspector.get_columns(table_name)]
                # Limpiar los nombres de columna del sufijo DESC para la verificación
                clean_cols = [col.split()[0] for col in columns]
                
                # Verificar si todas las columnas deseadas existen
                if all(col in cols_info for col in clean_cols):
                    cols_str = ", ".join(columns)
                    stmt = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({cols_str})"
                    try:
                        db.execute(text(stmt))
                        db.commit()
                        print(f"  [P0-MIGRATION] Índice '{index_name}' creado/verificado con éxito.")
                    except Exception as idx_err:
                        db.rollback()
                        print(f"  [P0-MIGRATION] Error creando índice '{index_name}': {idx_err}")
                else:
                    print(f"  [P0-MIGRATION] Omitido índice '{index_name}' porque no todas las columnas {columns} existen en '{table_name}'. Columnas en tabla: {cols_info}")

    print("[P0-MIGRATION] Migración y diagnóstico P0 finalizados.")
