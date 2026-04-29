import re
import asyncio
import httpx
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import Workspace, Folder, ProjectList, Task, User, Case, TaskChecklistItem, TaskComment

CLICKUP_API_URL = "https://api.clickup.com/api/v2"

async def fetch_clickup(endpoint: str, api_token: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(f"{CLICKUP_API_URL}/{endpoint}", headers=headers)
        if resp.status_code == 403:
            print(f"[ClickUp API Forbidden] {endpoint}: Saltando por falta de permisos.")
            return None
        if resp.status_code != 200:
            print(f"[ClickUp API Error] {endpoint}: {resp.status_code} - {resp.text}")
            resp.raise_for_status()
        return resp.json()

def normalize_status(clickup_status: str) -> str:
    s = clickup_status.lower().strip()
    if s in ['to do', 'todo', 'abierto', 'open', 'new', 'nueva']: return 'to do'
    if s in ['in progress', 'doing', 'en proceso', 'pendiente', 'en curso', 'desarrollo']: return 'in progress'
    if s in ['review', 'revisión', 'revisada', 'waiting', 'validación']: return 'review'
    if s in ['complete', 'completado', 'completada', 'closed', 'finalizado', 'finalizada', 'terminado', 'terminada']: return 'complete'
    return 'to do'

def extract_radicado(text: str) -> str:
    if not text: return None
    # Buscamos 21 a 23 dígitos pegados (formato radicado colombiano)
    normalized = re.sub(r'[\s\-.]', '', text)
    match = re.search(r'\d{21,23}', normalized)
    return match.group(0) if match else None

async def process_task(task_data: dict, list_id: int, db: Session, owner_id: int, user_map: dict, api_token: str, parent_id: int = None):
    """Procesa una tarea de ClickUp y sus subtareas recursivamente."""
    
    # 1. Mapear responsable
    assignee_id = None
    assignee_name = None
    if task_data.get('assignees'):
        main_assignee = task_data['assignees'][0]
        assignee_name = main_assignee.get('username')
        name_clean = (assignee_name or '').lower().strip()
        assignee_id = user_map.get(name_clean)
        
        # --- Lógica específica: Juan Jose Escobar -> jurico_emdecob ---
        if "juan" in name_clean and "escobar" in name_clean:
            juridico_user = db.query(User).filter(User.username == 'jurico_emdecob').first()
            if juridico_user:
                assignee_id = juridico_user.id

    # 2. Vinculación con Radicado Jurídico
    case_id = None
    radicado = extract_radicado(task_data['name'] + " " + (task_data.get('description') or ""))
    if radicado:
        # Intentamos encontrar por radicado exacto o que lo contenga
        matching_case = db.query(Case).filter(Case.radicado.like(f"%{radicado}%")).first()
        if matching_case:
            case_id = matching_case.id
        else:
            # SI NO EXISTE, lo creamos para que Juricob empiece a trackearlo
            # No le ponemos juzgado para que aparezca en "Pendientes" y el validador lo tome
            target_user_id = owner_id
            if assignee_id:
                target_user_id = assignee_id
                
            new_case = Case(radicado=radicado, user_id=target_user_id, demandado=task_data['name'])
            db.add(new_case)
            db.flush()
            case_id = new_case.id
            print(f"[ClickUp Sync] Nuevo radicado '{radicado}' creado desde tarea.")

    # 3. Mapear fechas
    due_date = None
    if task_data.get('due_date'):
        try:
            due_date = datetime.fromtimestamp(int(task_data['due_date']) / 1000.0)
        except: pass

    # 4. Crear o Actualizar Tarea Local (Master)
    existing_task = db.query(Task).filter(Task.clickup_id == task_data['id']).first()
    
    if existing_task:
        existing_task.title = task_data['name']
        existing_task.description = task_data.get('description')
        existing_task.status = normalize_status(task_data['status']['status'])
        existing_task.priority = task_data.get('priority', {}).get('priority') if task_data.get('priority') else None
        existing_task.due_date = due_date
        existing_task.case_id = case_id or existing_task.case_id
        existing_task.assignee_id = assignee_id or existing_task.assignee_id
        existing_task.assignee_name = assignee_name or existing_task.assignee_name
        existing_task.parent_id = parent_id or existing_task.parent_id
        db_task = existing_task
    else:
        db_task = Task(
            title=task_data['name'],
            description=task_data.get('description'),
            status=normalize_status(task_data['status']['status']),
            priority=task_data.get('priority', {}).get('priority') if task_data.get('priority') else None,
            clickup_id=task_data['id'],
            due_date=due_date,
            list_id=list_id,
            case_id=case_id,
            assignee_id=assignee_id,
            assignee_name=assignee_name,
            creator_id=owner_id,
            parent_id=parent_id
        )
        db.add(db_task)
    
    db.flush() # Para tener el ID local de la tarea para las subtareas

    # 5. Procesar Checklists (Listas de control)
    checklists = task_data.get('checklists', [])
    for cl in checklists:
        # Los items de checklist en ClickUp vienen en cl['items']
        for item in cl.get('items', []):
            existing_cl = db.query(TaskChecklistItem).filter(
                TaskChecklistItem.task_id == db_task.id,
                TaskChecklistItem.content == item['name']
            ).first()
            if not existing_cl:
                new_cl = TaskChecklistItem(
                    task_id=db_task.id,
                    content=item['name'],
                    is_completed=item.get('resolved', False)
                )
                db.add(new_cl)

    # 6. Procesar Comentarios (Solo si ClickUp indica que hay comentarios)
    if task_data.get('comment_count', 0) > 0:
        try:
            comments_data = await fetch_clickup(f"task/{task_data['id']}/comment", api_token)
            for comm in comments_data.get('comments', []):
                text_comm = comm.get('comment_text', '')
                if not text_comm: continue
                existing_comm = db.query(TaskComment).filter(TaskComment.task_id == db_task.id, TaskComment.content == text_comm).first()
                if not existing_comm:
                    new_comm = TaskComment(task_id=db_task.id, content=text_comm, user_id=owner_id)
                    db.add(new_comm)
        except: pass

    # 7. Procesar Subtareas
    subtasks = task_data.get('subtasks', [])
    for sub in subtasks:
        await process_task(sub, list_id, db, owner_id, user_map, api_token, parent_id=db_task.id)

async def migrate_clickup_to_emdecob(api_token: str, db: Session, owner_id: int):
    """Sincronización Maestra Juricob v2: Importación total y jerárquica."""
    
    print("[Master Sync] Iniciando importacion desde ClickUp...")
    
    # Cache de usuarios
    all_users = db.query(User).all()
    user_map = {u.nombre.lower().strip(): u.id for u in all_users if u.nombre}
    
    try:
        # 1. Teams (Workspaces)
        teams_data = await fetch_clickup("team", api_token)
        for team in teams_data['teams']:
            db_ws = db.query(Workspace).filter(Workspace.clickup_id == team['id']).first()
            if not db_ws:
                db_ws = Workspace(name=team['name'], clickup_id=team['id'], owner_id=owner_id)
                db.add(db_ws)
                db.flush()

            # 2. Spaces (Mapeados como Carpetas Raíz o Filtros)
            spaces_data = await fetch_clickup(f"team/{team['id']}/space", api_token)
            for space in spaces_data['spaces']:
                # Nota: Si el space tiene Carpetas, bajamos a ese nivel. Si tiene Listas directas, las tratamos.
                
                # 3. Folders (Abogados / Meses)
                folders_data = await fetch_clickup(f"space/{space['id']}/folder", api_token)
                for folder in folders_data['folders']:
                    db_folder = db.query(Folder).filter(Folder.clickup_id == folder['id']).first()
                    if not db_folder:
                        db_folder = Folder(name=folder['name'], clickup_id=folder['id'], workspace_id=db_ws.id)
                        db.add(db_folder)
                        db.flush()
                    
                    # 4. Lists
                    lists_data = await fetch_clickup(f"folder/{folder['id']}/list", api_token)
                    for lst in lists_data['lists']:
                        db_list = db.query(ProjectList).filter(ProjectList.clickup_id == lst['id']).first()
                        if not db_list:
                            db_list = ProjectList(name=lst['name'], clickup_id=lst['id'], folder_id=db_folder.id, workspace_id=db_ws.id)
                            db.add(db_list)
                            db.flush()
                        
                        # 5. Tasks & Subtasks
                        tasks_data = await fetch_clickup(f"list/{lst['id']}/task?subtasks=true&include_checklists=true&include_closed=true", api_token)
                        for t_data in tasks_data['tasks']:
                            await asyncio.sleep(0.1) # Pequeña pausa para evitar rate limits
                            await process_task(t_data, db_list.id, db, owner_id, user_map, api_token)
                        
                        db.commit() # Commit granular por lista
                        print(f"[Master Sync] Lista '{lst['name']}' procesada.")

                # 3.1 Listas sin carpeta (directas en el Space)
                space_lists_data = await fetch_clickup(f"space/{space['id']}/list", api_token)
                for lst in space_lists_data['lists']:
                    db_list = db.query(ProjectList).filter(ProjectList.clickup_id == lst['id']).first()
                    if not db_list:
                        # Creamos una carpeta 'General' para estas listas si no existe
                        db_folder = db.query(Folder).filter(Folder.name == "General", Folder.workspace_id == db_ws.id).first()
                        if not db_folder:
                            db_folder = Folder(name="General", workspace_id=db_ws.id)
                            db.add(db_folder)
                            db.flush()
                        
                        db_list = ProjectList(name=lst['name'], clickup_id=lst['id'], folder_id=db_folder.id, workspace_id=db_ws.id)
                        db.add(db_list)
                        db.flush()
                    
                    tasks_data = await fetch_clickup(f"list/{lst['id']}/task?subtasks=true&include_checklists=true", api_token)
                    for t_data in tasks_data['tasks']:
                        await process_task(t_data, db_list.id, db, owner_id, user_map, api_token)
                    db.commit()

        return {"status": "success", "message": "Importación maestra completada con éxito en Juricob."}
    
    except Exception as e:
        db.rollback()
        print(f"[Master Sync Error] {str(e)}")
        raise e
