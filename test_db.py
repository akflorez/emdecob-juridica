from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text("SELECT 1")).scalar()
    print("OK DB:", r)
