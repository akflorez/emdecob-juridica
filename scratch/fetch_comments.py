import asyncio
from backend.db import SessionLocal
from backend.models import Task, User
from backend.clickup_sync import fetch_clickup

async def main():
    db = SessionLocal()
    t = db.query(Task).filter(Task.id == 147).first()
    u = db.query(User).filter(User.clickup_token != None).first()
    print("ClickUp ID:", t.clickup_id if t else "No task")
    if t and t.clickup_id and u and u.clickup_token:
        res = await fetch_clickup(f"task/{t.clickup_id}/comment", u.clickup_token)
        print("Comments:", res)
    else:
        print("Missing token or clickup_id")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
