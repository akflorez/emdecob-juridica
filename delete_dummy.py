from backend.db import engine
from sqlalchemy import text

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    c.execute(text("DELETE FROM case_events WHERE title='Auto de prueba (AI)'"))
    print("Dummy event deleted")
