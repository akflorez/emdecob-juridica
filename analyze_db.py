import pandas as pd
from backend.db import engine
from sqlalchemy import text

with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
    print('--- Users ---')
    try:
        users = pd.read_sql(text('SELECT id, username, is_admin, company_id FROM users'), c)
        print(users)
    except Exception as e:
        print(e)
        
    print('\n--- Companies ---')
    try:
        companies = pd.read_sql(text('SELECT * FROM companies'), c)
        print(companies)
    except Exception as e:
        print(e)

    print('\n--- Cases Grouped by Company ---')
    try:
        cases_company = pd.read_sql(text('SELECT company_id, COUNT(*) FROM cases GROUP BY company_id'), c)
        print(cases_company)
    except Exception as e:
        print(e)
        
    print('\n--- Events Grouped by Date ---')
    try:
        events_date = pd.read_sql(text("SELECT event_date, COUNT(*) FROM case_events WHERE event_date >= '2026-06-01' GROUP BY event_date ORDER BY event_date DESC"), c)
        print(events_date)
    except Exception as e:
        print(e)
