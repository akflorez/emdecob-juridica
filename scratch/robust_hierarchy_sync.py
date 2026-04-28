
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Folder, ProjectList, Workspace

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")

def robust_sync():
    e_local = create_engine(LOCAL_DB)
    db_local = sessionmaker(bind=e_local)()

    e_prod = create_engine(NEON_URL)
    db_prod = sessionmaker(bind=e_prod)()

    # 1. Asegurar que el Workspace existe con nombre correcto
    ws_local = db_local.query(Workspace).filter(Workspace.id == 5).first()
    ws_prod = db_prod.query(Workspace).filter(Workspace.id == 1).first()
    
    # 2. Sync Folders
    local_folders = db_local.query(Folder).filter(Folder.workspace_id == 5).all()
    folder_mapping = {}
    for f in local_folders:
        try:
            existing = db_prod.query(Folder).filter(Folder.clickup_id == f.clickup_id).first()
            if not existing:
                print(f"Adding Folder: {f.name}")
                new_f = Folder(name=f.name, clickup_id=f.clickup_id, workspace_id=1)
                db_prod.add(new_f)
                db_prod.commit()
                folder_mapping[f.id] = new_f.id
            else:
                folder_mapping[f.id] = existing.id
        except Exception as e:
            print(f"Error skipping folder {f.name}: {e}")
            db_prod.rollback()

    # 3. Sync ProjectLists
    local_lists = db_local.query(ProjectList).filter(ProjectList.workspace_id == 5).all()
    for l in local_lists:
        try:
            existing = db_prod.query(ProjectList).filter(ProjectList.clickup_id == l.clickup_id).first()
            if not existing:
                target_folder_id = folder_mapping.get(l.folder_id)
                if target_folder_id:
                    print(f"Adding List: {l.name}")
                    new_l = ProjectList(name=l.name, clickup_id=l.clickup_id, folder_id=target_folder_id, workspace_id=1)
                    db_prod.add(new_l)
                    db_prod.commit()
        except Exception as e:
            print(f"Error skipping list {l.name}: {e}")
            db_prod.rollback()

    print("Robust sync complete!")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    robust_sync()
