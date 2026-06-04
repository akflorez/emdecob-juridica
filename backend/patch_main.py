import os

def run():
    with open('backend/migration_queries.sql', 'r', encoding='utf-8') as f:
        queries = f.read().splitlines()

    migration_code = "            # --- MIGRACION POSTGRESQL AUTOMATICA DE TODAS LAS TABLAS Y COLUMNAS ---\n"
    for q in queries:
        if q.strip():
            migration_code += f"            try: conn.execute(text(\"{q.strip()}\")); conn.commit()\n"
            migration_code += f"            except Exception: conn.rollback()\n"

    with open('backend/main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()

    # Find where to inject
    target = "    # --- AUTO-MIGRACIÓN SaaS POSTGRESQL INDEPENDIENTE ---"
    
    if target in main_content:
        new_content = main_content.replace(target, target + "\n        try:\n            pass\n" + migration_code)
        with open('backend/main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Patched main.py successfully.")
    else:
        print("Target not found.")

if __name__ == '__main__':
    run()
