
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import User, Workspace, WorkspaceMember, Folder, ProjectList

load_dotenv()
neon = os.getenv("NEON_URL")
engine = create_engine(neon)
Session = sessionmaker(bind=engine)
db = Session()

# Simular request para User 2
current_user = db.query(User).filter(User.id == 2).first()
print(f"Testing for user: {current_user.username} (Admin: {current_user.is_admin})")

try:
    if current_user.is_admin:
        workspaces = db.query(Workspace).all()
    else:
        workspaces = db.query(Workspace).join(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    
    print(f"Workspaces found: {len(workspaces)}")
    results = []
    for ws in workspaces:
        print(f"Processing WS: {ws.name}")
        folders = []
        for f in ws.folders:
            lists = [{"id": l.id, "name": l.name} for l in f.lists]
            folders.append({"id": f.id, "name": f.name, "lists": lists})
        
        results.append({
            "id": ws.id,
            "name": ws.name,
            "visibility": ws.visibility,
            "clickup_id": ws.clickup_id,
            "folders": folders
        })
    print("Success!")
except Exception as e:
    print(f"CRASH: {e}")
finally:
    db.close()
