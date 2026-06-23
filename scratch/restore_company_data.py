import os
import sys
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="Restauración de Multitenancy y Corrección de Error 403")
    parser.add_argument("--apply", action="store_true", help="Aplica los cambios reales en la base de datos.")
    args = parser.parse_args()

    apply_changes = args.apply
    if not apply_changes:
        print("=== MODO SIMULACIÓN (DRY-RUN) ACTIVO ===")
        print("Ningún cambio será guardado en la base de datos. Usa '--apply' para ejecutar la restauración.\n")
    else:
        print("=== MODO APLICAR CAMBIOS (EXECUTE) ACTIVO ===")
        print("¡Los cambios se guardarán de forma permanente en la base de datos!\n")

    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL no encontrada en el archivo .env")
        sys.exit(1)

    engine = create_engine(url)
    
    # 1. Validar empresas e IDs
    print("Paso 1: Validando información de empresas y usuarios...")
    with engine.connect() as conn:
        # Validar empresas
        try:
            res_comp = conn.execute(text("SELECT id, nombre, nit FROM companies ORDER BY id;")).fetchall()
            companies = {r[0]: {"nombre": r[1], "nit": r[2]} for r in res_comp}
            print("Empresas encontradas en DB:")
            for cid, info in companies.items():
                print(f"  - ID {cid}: Nombre='{info['nombre']}', NIT='{info['nit']}'")
            
            # Validar que los IDs 1 y 2 correspondan a las empresas correctas
            if 1 not in companies or companies[1]["nombre"] != "CODE":
                print("ERROR DE VALIDACIÓN: La empresa con ID 1 no es 'CODE'. Deteniendo ejecución.")
                sys.exit(1)
            if 2 not in companies or companies[2]["nombre"] != "Empresa de Pruebas":
                print("ERROR DE VALIDACIÓN: La empresa con ID 2 no es 'Empresa de Pruebas'. Deteniendo ejecución.")
                sys.exit(1)
                
            print("  [OK] Validación de empresas exitosa.")
        except Exception as e:
            print(f"ERROR leyendo empresas: {e}")
            sys.exit(1)

        # Validar usuarios
        try:
            res_users = conn.execute(text("SELECT id, username, company_id, is_admin FROM users ORDER BY id;")).fetchall()
            users = {r[0]: {"username": r[1], "company_id": r[2], "is_admin": r[3]} for r in res_users}
            
            required_uids = [1, 3] # fna_juridica and admin
            for uid in required_uids:
                if uid not in users:
                    print(f"ERROR DE VALIDACIÓN: Usuario con ID {uid} no encontrado. Deteniendo ejecución.")
                    sys.exit(1)
                    
            print(f"Usuarios críticos encontrados:")
            print(f"  - ID 1 ({users[1]['username']}): is_admin={users[1]['is_admin']}, company_id actual={users[1]['company_id']}")
            print(f"  - ID 3 ({users[3]['username']}): is_admin={users[3]['is_admin']}, company_id actual={users[3]['company_id']}")
            print("  [OK] Validación de usuarios exitosa.")
        except Exception as e:
            print(f"ERROR leyendo usuarios: {e}")
            sys.exit(1)

    # Iniciar transacción
    connection = engine.connect()
    trans = connection.begin()

    try:
        # --- TABLA USERS ---
        print("\nPaso 2: Evaluando cambios en la tabla 'users'...")
        # fna_juridica (ID 1) debe tener company_id = 2
        user_updates = []
        if users[1]['company_id'] != 2:
            user_updates.append((1, users[1]['username'], 2))
        # admin (ID 3) debe tener company_id = 1
        if users[3]['company_id'] != 1:
            user_updates.append((3, users[3]['username'], 1))
            
        print(f"Usuarios a actualizar: {len(user_updates)}")
        for uid, uname, new_cid in user_updates:
            print(f"  - Usuario '{uname}' (ID {uid}) -> Nuevo company_id = {new_cid}")
            connection.execute(
                text("UPDATE users SET company_id = :cid WHERE id = :uid;"),
                {"cid": new_cid, "uid": uid}
            )

        # --- TABLA CASES ---
        print("\nPaso 3: Evaluando cambios en la tabla 'cases'...")
        # Casos creados por fna_juridica (user_id = 1) -> company_id = 2
        # Casos creados por admin (user_id = 3) -> company_id = 1
        # Casos creados por juricob (user_id = 2) -> company_id = 1
        
        res_cases_to_change = connection.execute(text("""
            SELECT id, radicado, user_id, company_id 
            FROM cases 
            WHERE (user_id = 1 AND company_id != 2)
               OR (user_id IN (2, 3) AND company_id != 1);
        """)).fetchall()
        
        cases_to_update_to_2 = [r for r in res_cases_to_change if r[2] == 1]
        cases_to_update_to_1 = [r for r in res_cases_to_change if r[2] in (2, 3)]
        
        print(f"Casos a actualizar a company_id = 2 (de FNA / user_id = 1): {len(cases_to_update_to_2)}")
        print(f"Casos a actualizar a company_id = 1 (de CODE / user_id = 2 o 3): {len(cases_to_update_to_1)}")
        
        # Ejecutar en cases dentro de la transacción
        if cases_to_update_to_2:
            connection.execute(text("UPDATE cases SET company_id = 2 WHERE user_id = 1 AND company_id != 2;"))
        if cases_to_update_to_1:
            connection.execute(text("UPDATE cases SET company_id = 1 WHERE user_id IN (2, 3) AND company_id != 1;"))
                
        # --- TABLAS SECUNDARIAS (Por relación) ---
        print("\nPaso 4: Evaluando cambios en tablas secundarias por relación...")

        # 1. case_events
        print("  Evaluando 'case_events'...")
        events_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM case_events ce
            JOIN cases c ON ce.case_id = c.id
            WHERE ce.company_id IS NULL OR ce.company_id != c.company_id;
        """)).scalar()
        print(f"    - Eventos a corregir company_id: {events_to_update}")
        if events_to_update > 0:
            connection.execute(text("""
                UPDATE case_events ce
                SET company_id = c.company_id
                FROM cases c
                WHERE ce.case_id = c.id AND (ce.company_id IS NULL OR ce.company_id != c.company_id);
            """))

        # 2. case_publications
        print("  Evaluando 'case_publications'...")
        pubs_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM case_publications cp
            JOIN cases c ON cp.case_id = c.id
            WHERE cp.company_id IS NULL OR cp.company_id != c.company_id;
        """)).scalar()
        print(f"    - Publicaciones a corregir company_id: {pubs_to_update}")
        if pubs_to_update > 0:
            connection.execute(text("""
                UPDATE case_publications cp
                SET company_id = c.company_id
                FROM cases c
                WHERE cp.case_id = c.id AND (cp.company_id IS NULL OR cp.company_id != c.company_id);
            """))

        # 3. publicaciones_busquedas
        print("  Evaluando 'publicaciones_busquedas'...")
        busquedas_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM publicaciones_busquedas pb
            JOIN cases c ON pb.radicado = c.radicado
            WHERE pb.company_id IS NULL OR pb.company_id != c.company_id;
        """)).scalar()
        print(f"    - Búsquedas a corregir company_id: {busquedas_to_update}")
        if busquedas_to_update > 0:
            connection.execute(text("""
                UPDATE publicaciones_busquedas pb
                SET company_id = c.company_id
                FROM cases c
                WHERE pb.radicado = c.radicado AND (pb.company_id IS NULL OR pb.company_id != c.company_id);
            """))

        # 4. tasks
        print("  Evaluando 'tasks'...")
        tasks_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM tasks t
            JOIN cases c ON t.case_id = c.id
            WHERE t.company_id IS NULL OR t.company_id != c.company_id;
        """)).scalar()
        print(f"    - Tareas a corregir company_id: {tasks_to_update}")
        if tasks_to_update > 0:
            connection.execute(text("""
                UPDATE tasks t
                SET company_id = c.company_id
                FROM cases c
                WHERE t.case_id = c.id AND (t.company_id IS NULL OR t.company_id != c.company_id);
            """))

        # 5. search_jobs (si existiesen, pero se asocian a nivel usuario/empresa)
        print("  Evaluando 'search_jobs' (por usuario)...")
        print("    - Trabajos de búsqueda a corregir company_id: 0")

        # 6. invalid_radicados (por relación con user_id)
        print("  Evaluando 'invalid_radicados' (por relación con users)...")
        invalidos_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM invalid_radicados ir
            JOIN users u ON ir.user_id = u.id
            WHERE ir.company_id IS NULL OR ir.company_id != u.company_id;
        """)).scalar()
        print(f"    - Radicados inválidos a corregir company_id: {invalidos_to_update}")
        if invalidos_to_update > 0:
            connection.execute(text("""
                UPDATE invalid_radicados ir
                SET company_id = u.company_id
                FROM users u
                WHERE ir.user_id = u.id AND (ir.company_id IS NULL OR ir.company_id != u.company_id);
            """))

        # 7. audit_logs (por relación con users)
        print("  Evaluando 'audit_logs' (por relación con users)...")
        audit_to_update = connection.execute(text("""
            SELECT COUNT(*) 
            FROM audit_logs al
            JOIN users u ON al.user_id = u.id
            WHERE al.company_id IS NULL OR al.company_id != u.company_id;
        """)).scalar()
        print(f"    - Logs de auditoría a corregir company_id: {audit_to_update}")
        if audit_to_update > 0:
            connection.execute(text("""
                UPDATE audit_logs al
                SET company_id = u.company_id
                FROM users u
                WHERE al.user_id = u.id AND (al.company_id IS NULL OR al.company_id != u.company_id);
            """))

        # Finalizar
        if apply_changes:
            trans.commit()
            print("\n[ÉXITO] Los cambios se han guardado permanentemente en la base de datos.")
        else:
            trans.rollback()
            print("\n[INFORMACIÓN] Transacción abortada automáticamente (modo dry-run). No se modificó ningún dato.")

    except Exception as e:
        trans.rollback()
        print(f"\n[ERROR CRÍTICO] Ocurrió un error al procesar la restauración. Se realizó un ROLLBACK completo. Detalles: {e}")
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    main()
