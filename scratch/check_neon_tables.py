
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from backend.db import Base
from backend.models import User, Workspace, WorkspaceMember, Folder, ProjectList, Task, Case, CaseEvent # Import everything

load_dotenv()
neon = os.getenv("NEON_URL")
if not neon:
    exit("No NEON_URL")

engine = create_engine(neon)
Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    r = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
    print("Tables in Neon:", [row[0] for row in r])
