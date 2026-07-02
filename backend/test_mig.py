import os
import sys
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Base
from backend.db import DATABASE_URL

def get_sql_type(col, dialect):
    return str(col.type.compile(dialect=dialect))

def run():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    for table_name, table in Base.metadata.tables.items():
        print(f"Table: {table_name}")
        for col in table.columns:
            print(f"  {col.name}: {get_sql_type(col, engine.dialect)}")
            
if __name__ == "__main__":
    run()
