import time
from sqlalchemy import create_engine, text

URL_EMDECOB = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def main():
    print("Testing direct database connection to 84.247.130.122...")
    start = time.time()
    try:
        engine = create_engine(URL_EMDECOB, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            val = conn.execute(text("SELECT 1")).scalar()
            duration = time.time() - start
            print(f"Database connection successful! SELECT 1 returned {val} in {duration:.3f} seconds.")
    except Exception as e:
        duration = time.time() - start
        print(f"Database connection failed after {duration:.3f} seconds: {e}")

if __name__ == "__main__":
    main()
