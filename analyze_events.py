import pandas as pd
from backend.db import engine
from sqlalchemy import text

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    print('Total events:')
    try:
        total = pd.read_sql(text('SELECT COUNT(*) FROM case_events'), c)
        print(total)
    except Exception as e:
        print(e)
        
    print('\nMax event date:')
    try:
        dates = pd.read_sql(text('SELECT MAX(event_date) FROM case_events WHERE event_date < "3000-01-01"'), c)
        print(dates)
    except Exception as e:
        print(e)
