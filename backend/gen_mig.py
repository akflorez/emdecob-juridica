import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateColumn
from sqlalchemy.ext.compiler import compiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import Base


def run():
    # Creamos un engine postgres mock para compilar el dialecto correcto
    engine = create_engine("postgresql://user:pass@localhost/db")
    dialect = engine.dialect

    queries = []
    
    for table_name, table in Base.metadata.tables.items():
        for col in table.columns:
            # col.type.compile(dialect=dialect) gets the string type (e.g. VARCHAR(255))
            col_type = col.type.compile(dialect=dialect)
            # Default
            default = ""
            if col.default is not None and col.default.arg is not None:
                if isinstance(col.default.arg, (int, float, bool)):
                    default = f" DEFAULT {col.default.arg}"
                elif isinstance(col.default.arg, str):
                    default = f" DEFAULT '{col.default.arg}'"
            
            # Nullable
            # In ADD COLUMN we might avoid setting NOT NULL if there's no default to prevent errors on existing rows.
            # We'll just add the column and type and default.
            
            query = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col.name} {col_type}{default};"
            queries.append(query)

    with open("backend/migration_queries.sql", "w") as f:
        f.write("\n".join(queries))

if __name__ == "__main__":
    run()
