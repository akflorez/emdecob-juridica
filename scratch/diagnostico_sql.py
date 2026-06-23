import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# We will test both databases
databases = ["juricob", "emdecob_consultas"]
base_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/"
radicado = '11001400304820250059500'

for db_name in databases:
    db_url = base_url + db_name
    print(f"\n=========================================")
    print(f"DIAGNOSTICO PARA BASE DE DATOS: {db_name}")
    print(f"=========================================")
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 10})
        with engine.connect() as conn:
            # 1. publicaciones_busquedas
            print("--- 1. publicaciones_busquedas ---")
            query_1 = text("""
                SELECT id, company_id, radicado, mes_busqueda, fecha_inicio_busqueda, fecha_fin_busqueda,
                estado, intentos, ultimo_error, locked_at, processed_at, created_at, updated_at
                FROM publicaciones_busquedas
                WHERE radicado = :radicado
                ORDER BY created_at DESC;
            """)
            res_1 = conn.execute(query_1, {"radicado": radicado})
            cols_1 = res_1.keys()
            rows_1 = res_1.fetchall()
            print(f"Found {len(rows_1)} records:")
            for row in rows_1:
                row_dict = dict(zip(cols_1, row))
                if row_dict['ultimo_error']:
                    row_dict['ultimo_error'] = row_dict['ultimo_error'][:80] + "..." if len(row_dict['ultimo_error']) > 80 else row_dict['ultimo_error']
                print(row_dict)

            # 2. case_publications
            print("\n--- 2. case_publications ---")
            query_2 = text("""
                SELECT cp.id, cp.company_id, c.radicado, cp.fecha_publicacion, cp.numero_estado,
                cp.estado_validacion, cp.match_score, cp.match_type, cp.url_fuente_principal, cp.documento_url, cp.created_at
                FROM case_publications cp
                JOIN cases c ON cp.case_id = c.id
                WHERE c.radicado = :radicado
                ORDER BY cp.created_at DESC;
            """)
            res_2 = conn.execute(query_2, {"radicado": radicado})
            cols_2 = res_2.keys()
            rows_2 = res_2.fetchall()
            print(f"Found {len(rows_2)} publications:")
            for row in rows_2:
                print(dict(zip(cols_2, row)))

            # 3. publicaciones_busquedas (mes vacio)
            print("\n--- 3. publicaciones_busquedas (mes vacio) ---")
            query_3 = text("""
                SELECT id, company_id, radicado, mes_busqueda, estado, created_at
                FROM publicaciones_busquedas
                WHERE radicado = :radicado
                AND (mes_busqueda IS NULL OR mes_busqueda = '');
            """)
            res_3 = conn.execute(query_3, {"radicado": radicado})
            cols_3 = res_3.keys()
            rows_3 = res_3.fetchall()
            print(f"Found {len(rows_3)} empty month records:")
            for row in rows_3:
                print(dict(zip(cols_3, row)))
    except Exception as e:
        print(f"Error connecting/querying DB {db_name}: {e}")
