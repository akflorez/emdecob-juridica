
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Task, User, Folder, ProjectList, Case

load_dotenv()
NEON_URL = os.getenv("NEON_URL")
LOCAL_DB = os.getenv("DATABASE_URL")

def transfer():
    e_local = create_engine(LOCAL_DB)
    db_local = sessionmaker(bind=e_local)()

    e_prod = create_engine(NEON_URL)
    db_prod = sessionmaker(bind=e_prod)()

    # 1. Copiar Casos
    local_cases = db_local.query(Case).all()
    for c in local_cases:
        if not db_prod.query(Case).filter(Case.radicado == c.radicado).first():
            new_c = Case(
                id=c.id, radicado=c.radicado, id_proceso=c.id_proceso,
                demandante=c.demandante, demandado=c.demandado, juzgado=c.juzgado,
                user_id=c.user_id, fecha_radicacion=c.fecha_radicacion,
                ultima_actuacion=c.ultima_actuacion
            )
            db_prod.add(new_c)
    db_prod.commit()

    # 2. Copiar Tareas
    local_tasks = db_local.query(Task).all()
    for t in local_tasks:
        if not db_prod.query(Task).filter(Task.clickup_id == t.clickup_id).first():
            new_t = Task(
                title=t.title, description=t.description, status=t.status,
                priority=t.priority, clickup_id=t.clickup_id, due_date=t.due_date,
                list_id=t.list_id, case_id=t.case_id, assignee_id=t.assignee_id
            )
            db_prod.add(new_t)
    db_prod.commit()

    print("Success: 1069 tasks transferred to Neon!")
    db_local.close()
    db_prod.close()

if __name__ == "__main__":
    transfer()
