
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Folder, ProjectList, Workspace

load_dotenv()
neon = os.getenv("NEON_URL")
engine = create_engine(neon)
db = sessionmaker(bind=engine)()

def clean_text(text):
    if not text: return text
    return text.encode('ascii', 'ignore').decode('ascii')

print("Cleaning non-ASCII on Neon...")
for f in db.query(Folder).all():
    cleaned = clean_text(f.name)
    if cleaned != f.name:
        f.name = cleaned

for l in db.query(ProjectList).all():
    cleaned = clean_text(l.name)
    if cleaned != l.name:
        l.name = cleaned

for w in db.query(Workspace).all():
    cleaned = clean_text(w.name)
    if cleaned != w.name:
        w.name = cleaned

db.commit()
print("Cleaned!")
db.close()
