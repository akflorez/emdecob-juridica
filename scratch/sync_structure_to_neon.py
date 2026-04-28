
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import User, Workspace, WorkspaceMember, Folder, ProjectList, Task

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")

def sync():
    e_local = create_engine(LOCAL_DB)
    S_local = sessionmaker(bind=e_local)
    db_local = S_local()

    e_prod = create_engine(NEON_URL)
    S_prod = sessionmaker(bind=e_prod)
    db_prod = S_prod()

    # 1. Workspaces
    for item in db_local.query(Workspace).all():
        if not db_prod.query(Workspace).filter(Workspace.id == item.id).first():
            print(f"Syncing WS: {item.name}")
            new_item = Workspace(id=item.id, name=item.name, owner_id=item.owner_id, clickup_id=item.clickup_id)
            db_prod.add(new_item)
    db_prod.commit()

    # 2. Members
    for item in db_local.query(WorkspaceMember).all():
        if not db_prod.query(WorkspaceMember).filter(WorkspaceMember.id == item.id).first():
            new_item = WorkspaceMember(id=item.id, workspace_id=item.workspace_id, user_id=item.user_id, role=item.role)
            db_prod.add(new_item)
    db_prod.commit()

    # 3. Folders
    for item in db_local.query(Folder).all():
        if not db_prod.query(Folder).filter(Folder.id == item.id).first():
            new_item = Folder(id=item.id, name=item.name, workspace_id=item.workspace_id, clickup_id=item.clickup_id)
            db_prod.add(new_item)
    db_prod.commit()

    # 4. ProjectLists
    for item in db_local.query(ProjectList).all():
        if not db_prod.query(ProjectList).filter(ProjectList.id == item.id).first():
            new_item = ProjectList(id=item.id, name=item.name, folder_id=item.folder_id, workspace_id=item.workspace_id, clickup_id=item.clickup_id)
            db_prod.add(new_item)
    db_prod.commit()

    print("Structure sync to Neon complete!")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    sync()
