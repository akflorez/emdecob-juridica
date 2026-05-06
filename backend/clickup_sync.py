import re
import asyncio
import httpx
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import Workspace, Folder, ProjectList, Task, TaskChecklistItem, TaskComment, User, Case, Tag, TaskAttachment
import json

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
            return None
        return resp.json()

def normalize_status(status_data: any) -> str:
    # Retornar el estado original de ClickUp para mantener fidelidad total
    if isinstance(status_data, dict):
        return status_data.get('status', 'To Do')
    if isinstance(status_data, str):
        return status_data
    return 'To Do'

def extract_radicado(text: str) -> str:
    if not text: return None
    # Buscamos 21 a 23 dígitos pegados (formato radicado colombiano)
    normalized = re.sub(r'[\s\-.]', '', text)
    match = re.search(r'\d{21,23}', normalized)
    return match.group(0) if match else None

async def process_task(task_data: dict, list_id: int, db: Session, owner_id: int, user_map: dict, api_token: str, parent_id: int = None, inherited_case_id: int = None):
    """Procesa una tarea de ClickUp y sus subtareas recursivamente."""
    
    # 1. Mapear responsable (Múltiples)
    all_assignees_data = task_data.get('assignees', [])
    mapped_users = []
    assignee_names = []
    
    for a_data in all_assignees_data:
        a_name = a_data.get('username')
        if not a_name: continue
        assignee_names.append(a_name)
        name_clean = a_name.lower().strip()
        uid = user_map.get(name_clean)
        
        # Lógica específica: Juan Jose Escobar -> juricob / jurico_emdecob
        if not uid and "juan" in name_clean and "escobar" in name_clean:
            juridico_user = db.query(User).filter(User.username.in_(["juricob", "jurico_emdecob"])).first()
            if juridico_user: uid = juridico_user.id
            
        if uid:
            user_obj = db.query(User).filter(User.id == uid).first()
            if user_obj: mapped_users.append(user_obj)

    assignee_id = mapped_users[0].id if mapped_users else None
    assignee_name = ", ".join(assignee_names) if assignee_names else None

    # 2. Vinculación con Radicado Jurídico
    case_id = inherited_case_id
    radicado = extract_radicado(task_data['name'] + " " + (task_data.get('description') or ""))
    if radicado and not case_id:
        # Intentamos encontrar por radicado exacto o que lo contenga
        matching_case = db.query(Case).filter(Case.radicado.like(f"%{radicado}%")).first()
        if matching_case:
            case_id = matching_case.id
        else:
            # SI NO EXISTE, lo creamos para que Juricob empiece a trackearlo
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
    
    # Extraer status de forma robusta
    clickup_status = normalize_status(task_data.get('status'))
    
    if existing_task:
        existing_task.title = task_data['name']
        existing_task.description = task_data.get('description')
        existing_task.status = clickup_status
        existing_task.priority = task_data.get('priority', {}).get('priority') if task_data.get('priority') else None
        existing_task.due_date = due_date
        existing_task.case_id = case_id or existing_task.case_id
        existing_task.assignee_id = assignee_id
        existing_task.assignee_name = assignee_name
        existing_task.assignees = mapped_users
        existing_task.parent_id = parent_id or existing_task.parent_id
        db_task = existing_task
    else:
        db_task = Task(
            title=task_data['name'],
            description=task_data.get('description'),
            status=clickup_status,
            priority=task_data.get('priority', {}).get('priority') if task_data.get('priority') else None,
            clickup_id=task_data['id'],
            due_date=due_date,
            list_id=list_id,
            case_id=case_id,
            assignee_id=assignee_id,
            assignee_name=assignee_name,
            assignees=mapped_users,
            creator_id=owner_id,
            parent_id=parent_id,
            custom_fields=json.dumps(task_data.get('custom_fields', []))
        )
        db.add(db_task)
    
    db.flush() 

    # 5. Procesar Checklists (Listas de control)
    checklists = task_data.get('checklists', [])
    for cl in checklists:
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

    # 6. Procesar Comentarios (Fidelidad de Histórico)
    try:
        # Intentamos traer comentarios siempre para asegurar histórico completo
        comments_data = await fetch_clickup(f"task/{task_data['id']}/comment", api_token)
        if comments_data and 'comments' in comments_data:
            for comm in comments_data.get('comments', []):
                text_comm = comm.get('comment_text', '')
                if not text_comm: continue
                # Evitar duplicados por contenido
                existing_comm = db.query(TaskComment).filter(TaskComment.task_id == db_task.id, TaskComment.content == text_comm).first()
                if not existing_comm:
                    # Intentamos usar el nombre del usuario de ClickUp si está disponible
                    user_info = comm.get('user', {})
                    u_name = user_info.get('username', 'SISTEMA (CU)')
                    new_comm = TaskComment(
                        task_id=db_task.id, 
                        content=text_comm, 
                        user_id=owner_id,
                        user_name=u_name
                    )
                    db.add(new_comm)
    except Exception as e:
        print(f"[ClickUp Sync] Error en comentarios: {e}")

    # 6.2 Procesar Adjuntos (Attachments) de ClickUp
    attachments = task_data.get('attachments', [])
    for att in attachments:
        existing_att = db.query(TaskAttachment).filter(
            TaskAttachment.task_id == db_task.id, 
            TaskAttachment.name == att['title']
        ).first()
        if not existing_att:
            new_att = TaskAttachment(
                task_id=db_task.id,
                name=att['title'],
                file_path=att['url'],
                file_type=att.get('extension')
            )
            db.add(new_att)

    # 6.5 Procesar Etiquetas (Tags)
    clickup_tags = task_data.get('tags', [])
    if clickup_tags:
        db_tags = []
        for tag_data in clickup_tags:
            tag_name = tag_data.get('name')
            if not tag_name: continue
            db_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not db_tag:
                db_tag = Tag(name=tag_name, color=tag_data.get('tag_bg', '#3b82f6'))
                db.add(db_tag)
                db.flush()
            db_tags.append(db_tag)
        db_task.tags = db_tags
        db.flush()

    # 7. Procesar Subtareas (Recursividad con fidelidad de estado)
    subtasks = task_data.get('subtasks', [])
    for sub in subtasks:
        # Aseguramos que la subtarea herede el radicado si no tiene uno propio
        await process_task(sub, list_id, db, owner_id, user_map, api_token, parent_id=db_task.id, inherited_case_id=case_id)

async def migrate_clickup_to_emdecob(api_token: str, db: Session, owner_id: int):
    """Sincronización Maestra Juricob v2: Importación total y jerárquica."""
    
    print("[Master Sync] Iniciando importacion desde ClickUp...")
    
    # Cache de usuarios
    all_users = db.query(User).all()
    user_map = { (u.nombre or '').lower().strip(): u.id for u in all_users if u.nombre }
    user_map.update({ (u.username or '').lower().strip(): u.id for u in all_users if u.username })
    
    try:
        # 1. Teams (Workspaces)
        teams_data = await fetch_clickup("team", api_token)
        if not teams_data: return
        
        for team in teams_data['teams']:
            # --- SINCRONIZACIÓN DE ABOGADOS (ClickUp Members) ---
            for member in team.get('members', []):
                m_user = member.get('user', {})
                m_name = m_user.get('username')
                if not m_name: continue
                
                m_name_clean = m_name.lower().strip()
                if m_name_clean not in user_map:
                    existing = db.query(User).filter(User.nombre == m_name).first()
                    if not existing:
                        new_u = User(
                            username=f"cu_{m_user.get('id')}", 
                            nombre=m_name,
                            email=m_user.get('email'),
                            is_active=True,
                            is_admin=False,
                            hashed_password="clickup_placeholder"
                        )
                        db.add(new_u)
                        db.flush()
                        user_map[m_name_clean] = new_u.id
                    else:
                        user_map[m_name_clean] = existing.id

            db_ws = db.query(Workspace).filter(Workspace.clickup_id == team['id']).first()
            if not db_ws:
                db_ws = Workspace(name=team['name'], clickup_id=team['id'], owner_id=owner_id)
                db.add(db_ws)
                db.flush()

            # 2. Spaces
            spaces_data = await fetch_clickup(f"team/{team['id']}/space", api_token)
            if not spaces_data: continue
            
            for space in spaces_data['spaces']:
                # 3. Folders
                folders_data = await fetch_clickup(f"space/{space['id']}/folder", api_token)
                if folders_data:
                    for folder in folders_data['folders']:
                        db_folder = db.query(Folder).filter(Folder.clickup_id == folder['id']).first()
                        if not db_folder:
                            db_folder = Folder(name=folder['name'], clickup_id=folder['id'], workspace_id=db_ws.id)
                            db.add(db_folder)
                            db.flush()
                        
                        # 4. Lists
                        lists_data = await fetch_clickup(f"folder/{folder['id']}/list", api_token)
                        if lists_data:
                            for lst in lists_data['lists']:
                                db_list = db.query(ProjectList).filter(ProjectList.clickup_id == lst['id']).first()
                                if not db_list:
                                    db_list = ProjectList(name=lst['name'], clickup_id=lst['id'], folder_id=db_folder.id, workspace_id=db_ws.id)
                                    db.add(db_list)
                                    db.flush()
                                
                                # 5. Tasks & Subtasks (IMPORTANTE: include_closed=true)
                                tasks_data = await fetch_clickup(f"list/{lst['id']}/task?subtasks=true&include_checklists=true&include_closed=true", api_token)
                                if tasks_data and 'tasks' in tasks_data:
                                    for t_data in tasks_data['tasks']:
                                        await asyncio.sleep(0.05)
                                        await process_task(t_data, db_list.id, db, owner_id, user_map, api_token)
                                    db.commit()

                # 3.1 Listas sin carpeta
                space_lists_data = await fetch_clickup(f"space/{space['id']}/list", api_token)
                if space_lists_data:
                    for lst in space_lists_data['lists']:
                        db_list = db.query(ProjectList).filter(ProjectList.clickup_id == lst['id']).first()
                        if not db_list:
                            db_list = ProjectList(name=lst['name'], clickup_id=lst['id'], workspace_id=db_ws.id)
                            db.add(db_list)
                            db.flush()
                        
                        tasks_data = await fetch_clickup(f"list/{lst['id']}/task?subtasks=true&include_checklists=true&include_closed=true", api_token)
                        if tasks_data and 'tasks' in tasks_data:
                            for t_data in tasks_data['tasks']:
                                await process_task(t_data, db_list.id, db, owner_id, user_map, api_token)
                            db.commit()

    except Exception as e:
        print(f"[Master Sync Error] {e}")
        db.rollback()
