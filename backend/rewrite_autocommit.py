import os

def rewrite_migrations_autocommit():
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace "with engine.connect() as conn:" with "with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:" inside lifespan
    # But only the one inside lifespan.
    # Also replace try: conn.execute(...); conn.commit() with try: conn.execute(...) except...
    
    # Actually, it's easier to just do a regex or string replacement for the try...except blocks.
    
    # 1. change the connection
    content = content.replace(
        "    try:\n        with engine.connect() as conn:\n            # --- MIGRACION POSTGRESQL AUTOMATICA DE TODAS LAS TABLAS Y COLUMNAS ---",
        "    try:\n        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:\n            # --- MIGRACION POSTGRESQL AUTOMATICA DE TODAS LAS TABLAS Y COLUMNAS ---"
    )
    
    # 2. change the statements
    import re
    # We want to replace:
    # try: conn.execute(text("...")); conn.commit()
    # except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}'); conn.rollback()
    
    pattern = re.compile(r"try: conn\.execute\(text\((.*?)\)\); conn\.commit\(\)\n\s*except Exception as e: print\(f'\[AUTO-MIGRATE ERROR\] \{e\}'\); conn\.rollback\(\)")
    
    new_content = pattern.sub(r"try: conn.execute(text(\1))\n            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')", content)

    # 3. For the old un-logged version (just in case)
    pattern2 = re.compile(r"try: conn\.execute\(text\((.*?)\)\); conn\.commit\(\)\n\s*except Exception: conn\.rollback\(\)")
    new_content = pattern2.sub(r"try: conn.execute(text(\1))\n            except Exception as e: print(f'[AUTO-MIGRATE ERROR] {e}')", new_content)

    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    rewrite_migrations_autocommit()
