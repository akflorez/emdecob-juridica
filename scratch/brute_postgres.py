
import sqlalchemy
from sqlalchemy import create_engine, text

passwords = ["emdecob2026", "Emdecob2026*", "margarita1393", "juridicaEmdecob2026$"]

for p in passwords:
    url = f"postgresql://emdecob:{p}@127.0.0.1:5432/juricob"
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print(f"SUCCESS with password: {p}")
            res = conn.execute(text("SELECT COUNT(*) FROM cases"))
            print(f"Cases: {res.scalar()}")
            break
    except Exception as e:
        print(f"Failed with {p}")
