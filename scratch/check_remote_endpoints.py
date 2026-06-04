import base64
import json
import time
import httpx
import asyncio
from cryptography.fernet import Fernet

SECRET_KEY_DEV = base64.urlsafe_b64encode(b'emdecob_secret_jwt_key_123456789')
fernet = Fernet(SECRET_KEY_DEV)

def create_access_token(user_id: int) -> str:
    payload = json.dumps({"user_id": user_id}).encode('utf-8')
    return fernet.encrypt(payload).decode('utf-8')

async def test_endpoint(name, url, headers):
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(url, headers=headers)
            duration = time.time() - start
            print(f"[{name}] GET {url} -> status={resp.status_code} | duration={duration:.3f}s | length={len(resp.text)}")
    except Exception as e:
        duration = time.time() - start
        print(f"[{name}] GET {url} -> Failed after {duration:.3f}s: {e}")

async def main():
    token = create_access_token(2)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # We will test two database endpoints
    print("Testing production endpoints response times...")
    await test_endpoint("Task List", "http://84.247.130.122:8090/api/projects/tasks", headers)
    await test_endpoint("Cases List", "http://84.247.130.122:8090/api/cases", headers) # Let's try cases endpoint
    
if __name__ == "__main__":
    asyncio.run(main())
