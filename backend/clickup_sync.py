import httpx
from sqlalchemy.orm import Session
from .models import Workspace, WorkspaceMember, Folder, ProjectList, Task, User
import asyncio

CLICKUP_API_URL = "https://api.clickup.com/api/v2"

async def get_clickup_teams(api_token: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLICKUP_API_URL}/team", headers=headers)
        resp.raise_for_status()
        return resp.json()["teams"]

async def get_clickup_spaces(api_token: str, team_id: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLICKUP_API_URL}/team/{team_id}/space", headers=headers)
        resp.raise_for_status()
        return resp.json()["spaces"]

async def get_clickup_folders(api_token: str, space_id: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLICKUP_API_URL}/space/{space_id}/folder", headers=headers)
        resp.raise_for_status()
        return resp.json()["folders"]

async def get_clickup_lists(api_token: str, folder_id: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLICKUP_API_URL}/folder/{folder_id}/list", headers=headers)
        resp.raise_for_status()
        return resp.json()["lists"]

async def get_clickup_tasks(api_token: str, list_id: str):
    headers = {"Authorization": api_token}
    async with httpx.AsyncClient() as client:
        # We fetch including subtasks
        resp = await client.get(f"{CLICKUP_API_URL}/list/{list_id}/task?subtasks=true", headers=headers)
        resp.raise_for_status()
        return resp.json()["tasks"]

async def migrate_clickup_to_emdecob(api_token: str, db: Session, owner_id: int):
    """
    Realiza la migración completa desde ClickUp.
    Mapeo: 
    Team -> Workspace
    Space -> Folder (o nivel superior)
    Folder -> Folder
    List -> ProjectList
    Task -> Task
    """
    
    # 1. Obtener Teams (Workspaces en ClickUp)
    teams = await get_clickup_teams(api_token)
    
    # Cache de usuarios para mapeo rápido por nombre
    all_users = db.query(User).all()
    user_map = {u.nombre.lower().strip(): u.id for u in all_users if u.nombre}

    results = []

    for team in teams:
        print(f"Migrando Team: {team['name']}")
        
        # Crear Workspace
        workspace = db.query(Workspace).filter(Workspace.name == team['name']).first()
        if not workspace:
            workspace = Workspace(name=team['name'], owner_id=owner_id)
            db.add(workspace)
            db.flush()
        
        # 2. Obtener Spaces
        spaces = await get_clickup_spaces(api_token, team['id'])
        for space in spaces:
            # En ClickUp, los Spaces pueden tener Folders o Lists directas.
            # Aquí los trataremos como Folders raíz si tienen folders dentro.
            
            # 3. Obtener Folders
            folders = await get_clickup_folders(api_token, space['id'])
            for folder in folders:
                db_folder = db.query(Folder).filter(Folder.name == folder['name'], Folder.workspace_id == workspace.id).first()
                if not db_folder:
                    db_folder = Folder(name=folder['name'], workspace_id=workspace.id)
                    db.add(db_folder)
                    db.flush()
                
                # 4. Obtener Lists
                lists = await get_clickup_lists(api_token, folder['id'])
                for lst in lists:
                    db_list = db.query(ProjectList).filter(ProjectList.name == lst['name'], ProjectList.folder_id == db_folder.id).first()
                    if not db_list:
                        db_list = ProjectList(name=lst['name'], folder_id=db_folder.id, workspace_id=workspace.id)
                        db.add(db_list)
                        db.flush()
                    
                    # 5. Obtener Tareas
                    tasks = await get_clickup_tasks(api_token, lst['id'])
                    for task in tasks:
                        # Evitar duplicados por clickup_id
                        existing_task = db.query(Task).filter(Task.clickup_id == task['id']).first()
                        if existing_task:
                            continue
                        
                        # Mapear responsable
                        assignee_id = None
                        if task.get('assignees'):
                            main_assignee_name = task['assignees'][0]['username'].lower().strip()
                            assignee_id = user_map.get(main_assignee_name)

                        db_task = Task(
                            title=task['name'],
                            description=task.get('description'),
                            status=task['status']['status'],
                            priority=task.get('priority', {}).get('priority') if task.get('priority') else None,
                            clickup_id=task['id'],
                            list_id=db_list.id,
                            assignee_id=assignee_id,
                            creator_id=owner_id
                        )
                        db.add(db_task)
            
    db.commit()
    return {"status": "success", "message": "Migración completada"}
