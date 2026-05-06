
from backend.db import SessionLocal
from backend.models import Workspace, WorkspaceMember, User

def check():
    db = SessionLocal()
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == 2).all()
    print(f"Workspaces where User ID 2 is a member: {len(memberships)}")
    for m in memberships:
        ws = db.query(Workspace).filter(Workspace.id == m.workspace_id).first()
        print(f"  WS ID: {ws.id}, Name: {ws.name}, Role: {m.role}")
    
    all_ws = db.query(Workspace).all()
    print(f"\nTotal Workspaces in DB: {len(all_ws)}")
    for ws in all_ws:
        print(f"  WS ID: {ws.id}, Name: {ws.name}")
    
    db.close()

if __name__ == "__main__":
    check()
