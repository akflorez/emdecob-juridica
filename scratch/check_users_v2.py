from sqlalchemy import create_engine, text

url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(url)
with engine.connect() as conn:
    users = conn.execute(text("SELECT id, username, email FROM users ORDER BY id")).fetchall()
    print("Users in emdecob_consultas:")
    for u in users:
        print(f"  ID: {u[0]}, username: {u[1]}, email: {u[2]}")
