import os

def fix():
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1

    for i, line in enumerate(lines):
        if "    # --- AUTO-MIGRACIÓN SaaS POSTGRESQL INDEPENDIENTE ---" in line:
            start_idx = i + 1
            break
            
    for i in range(start_idx, len(lines)):
        # find the original try:
        if "    try:" in lines[i] and "        with engine.connect() as conn:" in lines[i+1]:
            end_idx = i
            break

    print(f"Start: {start_idx}, End: {end_idx}")
    
    if start_idx != -1 and end_idx != -1:
        # Get the queries
        with open('backend/migration_queries.sql', 'r', encoding='utf-8') as f:
            queries = f.read().splitlines()

        migration_code = ["            # --- MIGRACION POSTGRESQL AUTOMATICA DE TODAS LAS TABLAS Y COLUMNAS ---\n"]
        for q in queries:
            if q.strip():
                migration_code.append(f"            try: conn.execute(text(\"{q.strip()}\")); conn.commit()\n")
                migration_code.append(f"            except Exception: conn.rollback()\n")

        # Now put migration_code AFTER the "with engine.connect() as conn:"
        # So we delete lines from start_idx to end_idx-1
        
        del lines[start_idx:end_idx]
        
        # Now find the "with engine.connect() as conn:"
        for i in range(start_idx, len(lines)):
            if "        with engine.connect() as conn:" in lines[i]:
                # insert after this line
                insert_idx = i + 1
                for j, mc in enumerate(migration_code):
                    lines.insert(insert_idx + j, mc)
                break
                
        with open('backend/main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Fixed main.py")
        
if __name__ == '__main__':
    fix()
