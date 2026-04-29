
import sqlalchemy
from sqlalchemy import create_engine, text

users = ["emdecob", "postgres", "admin"]
passwords = ["emdecob2026", "Emdecob2026*", "root", "password", "123456"]

for u in users:
    for p in passwords:
        url = f"postgresql://{u}:{p}@127.0.0.1:5432/postgres"
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                print(f"SUCCESS with {u}:{p}")
                res = conn.execute(text("SELECT datname FROM pg_database"))
                print(f"Databases: {[r[0] for r in res]}")
                exit(0)
        except:
            pass
print("No credentials worked")
