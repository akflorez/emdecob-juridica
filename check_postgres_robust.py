import os
from sqlalchemy import create_engine, text

# Try different common combinations for local postgres
urls = [
    "postgresql://emdecob:emdecob2026@localhost:5432/juricob",
    "postgresql://postgres:emdecob2026@localhost:5432/juricob",
    "postgresql://emdecob:emdecob2026@127.0.0.1:5432/juricob"
]

for url in urls:
    print(f"Testing {url}...")
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT count(*) FROM cases"))
            count = res.scalar()
            print(f"SUCCESS! Cases: {count}")
            
            res = conn.execute(text("SELECT MAX(created_at) FROM cases"))
            max_date = res.scalar()
            print(f"Latest record: {max_date}")
            break
    except Exception as e:
        print(f"Failed: {type(e).__name__}")
