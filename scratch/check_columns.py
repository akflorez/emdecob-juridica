from sqlalchemy import create_engine, text

dbs = ["juricob", "emdecob_consultas", "postgres"]

for db_name in dbs:
    url = f"postgresql://emdecob:emdecob2026@84.247.130.122:5432/{db_name}"
    print(f"\n--- Checking DB: {db_name} ---")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            # Check table existence
            table_check = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'users'
                );
            """)).scalar()
            print(f"Table 'users' exists: {table_check}")
            if table_check:
                columns = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users';
                """)).fetchall()
                print("Columns:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
    except Exception as e:
        print(f"Error checking {db_name}: {e}")
