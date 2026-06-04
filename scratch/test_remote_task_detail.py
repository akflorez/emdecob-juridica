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

async def main():
    # User ID 2 is a valid user in emdecob_consultas
    token = create_access_token(2)
    print(f"Generated Token: {token[:40]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-ClickUp-Token": "pk_test_invalid_token_for_testing",
        "Content-Type": "application/json"
    }
    
    # We will test task ID 5093 (which has a ClickUp ID in emdecob_consultas)
    url = "http://84.247.130.122:8090/api/tasks/5093"
    
    print(f"\nSending request to remote backend: GET {url}")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=45.0, verify=False) as client:
            resp = await client.get(url, headers=headers)
            duration = time.time() - start
            print(f"Response status: {resp.status_code}")
            print(f"Duration: {duration:.3f} seconds")
            print(f"Body: {resp.text[:400]}")
            
            if duration < 0.5:
                print("\n✅ SUCCESS: The remote backend responded instantly. It is running the optimized background-sync code!")
            else:
                print("\n❌ LATE RESPONSE: The remote backend took long. It is likely still running the old synchronous-sync code.")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
