from sqlalchemy import create_engine, text

dbs = ["juricob", "emdecob_consultas"]

for db_name in dbs:
    url = f"postgresql://emdecob:emdecob2026@84.247.130.122:5432/{db_name}"
    print(f"\n--- Checking DB: {db_name} ---")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            for table in ["users", "cases", "tasks", "companies"]:
                # check if table exists first
                exists = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = '{table}'
                    );
                """)).scalar()
                if exists:
                    count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar()
                    print(f"Table '{table}' row count: {count}")
                else:
                    print(f"Table '{table}' does NOT exist")
    except Exception as e:
        print(f"Error checking {db_name}: {e}")
