
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import User, Workspace, WorkspaceMember, Folder, ProjectList, Task, Case, CaseEvent

load_dotenv()
LOCAL_DB = os.getenv("DATABASE_URL")
# USANDO EL NOMBRE REAL DE LA BASE DE DATOS EN EL SERVIDOR
CONTABO_PG = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"

def full_sync_to_contabo():
    e_local = create_engine(LOCAL_DB)
    db_local = sessionmaker(bind=e_local)()

    print(f"Connecting to Contabo DB emdecob_consultas...")
    e_prod = create_engine(CONTABO_PG)
    db_prod = sessionmaker(bind=e_prod)()

    # 1. Sync Users
    print("Syncing Users...")
    for u in db_local.query(User).all():
        if not db_prod.query(User).filter(User.username == u.username).first():
            print(f"  Adding User: {u.username}")
            new_u = User(id=u.id, username=u.username, hashed_password=u.hashed_password, is_admin=u.is_admin, nombre=u.nombre)
            db_prod.add(new_u)
    db_prod.commit()

    # 2. Sync Workspaces & Members
    print("Syncing Workspaces...")
    for ws in db_local.query(Workspace).all():
        if not db_prod.query(Workspace).filter(Workspace.clickup_id == ws.clickup_id).first():
            print(f"  Adding WS: {ws.name}")
            new_ws = Workspace(id=ws.id, name=ws.name, owner_id=ws.owner_id, clickup_id=ws.clickup_id, visibility=ws.visibility)
            db_prod.add(new_ws)
    db_prod.commit()

    for m in db_local.query(WorkspaceMember).all():
        if not db_prod.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == m.workspace_id, WorkspaceMember.user_id == m.user_id).first():
            new_m = WorkspaceMember(workspace_id=m.workspace_id, user_id=m.user_id, role=m.role)
            db_prod.add(new_m)
    db_prod.commit()

    # 3. Sync Folders & Lists
    print("Syncing Hierarchy...")
    for f in db_local.query(Folder).all():
        if not db_prod.query(Folder).filter(Folder.clickup_id == f.clickup_id).first():
            new_f = Folder(id=f.id, name=f.name, workspace_id=f.workspace_id, clickup_id=f.clickup_id)
            db_prod.add(new_f)
    db_prod.commit()

    for l in db_local.query(ProjectList).all():
        if not db_prod.query(ProjectList).filter(ProjectList.clickup_id == l.clickup_id).first():
            new_l = ProjectList(id=l.id, name=l.name, folder_id=l.folder_id, workspace_id=l.workspace_id, clickup_id=l.clickup_id)
            db_prod.add(new_l)
    db_prod.commit()

    # 4. Sync Cases
    print("Syncing Cases...")
    for c in db_local.query(Case).all():
        if not db_prod.query(Case).filter(Case.radicado == c.radicado).first():
            new_c = Case(
                id=c.id, radicado=c.radicado, id_proceso=c.id_proceso,
                demandante=c.demandante, demandado=c.demandado, juzgado=c.juzgado,
                user_id=c.user_id, fecha_radicacion=c.fecha_radicacion,
                ultima_actuacion=c.ultima_actuacion
            )
            db_prod.add(new_c)
    db_prod.commit()

    # 5. Sync Tasks
    print("Syncing Tasks...")
    for t in db_local.query(Task).all():
        if not db_prod.query(Task).filter(Task.clickup_id == t.clickup_id).first():
            new_t = Task(
                id=t.id, title=t.title, description=t.description, status=t.status,
                priority=t.priority, clickup_id=t.clickup_id, due_date=t.due_date,
                list_id=t.list_id, case_id=t.case_id, assignee_id=2 # Forzar asignacion a jurico_emdecob
            )
            db_prod.add(new_t)
    db_prod.commit()

    # 6. Sync Events (Actuaciones)
    print("Syncing Events...")
    count = 0
    for ev in db_local.query(CaseEvent).all():
        if not db_prod.query(CaseEvent).filter(CaseEvent.case_id == ev.case_id, CaseEvent.event_hash == ev.event_hash).first():
            new_ev = CaseEvent(
                case_id=ev.case_id, event_date=ev.event_date,
                title=ev.title, detail=ev.detail, event_hash=ev.event_hash,
                con_documentos=ev.con_documentos
            )
            db_prod.add(new_ev)
            count += 1
            if count % 100 == 0:
                db_prod.commit()
                print(f"  {count} events uploaded...")

    db_prod.commit()
    print(f"Success: {count} events and structure transferred to Contabo emdecob_consultas!")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    full_sync_to_contabo()
