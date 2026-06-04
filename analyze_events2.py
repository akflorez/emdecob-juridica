import pandas as pd
from backend.db import engine
from sqlalchemy import text

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    print('Max event date:')
    try:
        dates = pd.read_sql(text("SELECT MAX(event_date) FROM case_events WHERE event_date < '3000-01-01'"), c)
        print(dates)
    except Exception as e:
        print(e)
    
    print('\nEvents in May 2026:')
    try:
        may_events = pd.read_sql(text("SELECT event_date, COUNT(*) FROM case_events WHERE event_date >= '2026-05-01' AND event_date < '2026-06-01' GROUP BY event_date ORDER BY event_date DESC"), c)
        print(may_events)
    except Exception as e:
        print(e)
