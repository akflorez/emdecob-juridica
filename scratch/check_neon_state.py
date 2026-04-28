
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import User, Task

load_dotenv()
neon = os.getenv("NEON_URL")
engine = create_engine(neon)
Session = sessionmaker(bind=engine)
db = Session()

u = db.query(User).filter(User.id == 2).first()
task_count = db.query(Task).filter(Task.assignee_id == 2).count()

print(f"Neon Database Check:")
print(f"- User 2 (jurico_emdecob): {'Found' if u else 'Not Found'}")
print(f"- Tasks assigned to User 2: {task_count}")
db.close()
