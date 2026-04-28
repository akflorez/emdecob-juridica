
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Folder, ProjectList

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")

def copy_hierarchy():
    e_local = create_engine(LOCAL_DB)
    S_local = sessionmaker(bind=e_local)
    db_local = S_local()

    e_prod = create_engine(NEON_URL)
    S_prod = sessionmaker(bind=e_prod)
    db_prod = S_prod()

    # Mapeo WS local 5 -> WS neon 1
    # Folders de WS 5
    local_folders = db_local.query(Folder).filter(Folder.workspace_id == 5).all()
    for f in local_folders:
        existing = db_prod.query(Folder).filter(Folder.clickup_id == f.clickup_id).first()
        if not existing:
            print(f"Copying Folder: {f.name}")
            new_f = Folder(name=f.name, clickup_id=f.clickup_id, workspace_id=1)
            db_prod.add(new_f)
            db_prod.flush()
            
            # ProjectLists de este folder
            local_lists = db_local.query(ProjectList).filter(ProjectList.folder_id == f.id).all()
            for l in local_lists:
                new_l = ProjectList(name=l.name, clickup_id=l.clickup_id, folder_id=new_f.id, workspace_id=1)
                db_prod.add(new_l)
        else:
            # Si folder existe, asegurar que listas esten
            local_lists = db_local.query(ProjectList).filter(ProjectList.folder_id == f.id).all()
            for l in local_lists:
                lexist = db_prod.query(ProjectList).filter(ProjectList.clickup_id == l.clickup_id).first()
                if not lexist:
                    print(f"Copying List: {l.name}")
                    new_l = ProjectList(name=l.name, clickup_id=l.clickup_id, folder_id=existing.id, workspace_id=1)
                    db_prod.add(new_l)
                    
    db_prod.commit()
    print("Hierarchy copy complete!")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    copy_hierarchy()
