import base64
import json
import httpx
import traceback
import asyncio
from cryptography.fernet import Fernet

SECRET_KEY_DEV = base64.urlsafe_b64encode(b'emdecob_secret_jwt_key_123456789')
fernet = Fernet(SECRET_KEY_DEV)

def create_access_token(user_id: int) -> str:
    payload = json.dumps({"user_id": user_id}).encode('utf-8')
    return fernet.encrypt(payload).decode('utf-8')

async def main():
    token = create_access_token(2)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-ClickUp-Token": "pk_test_invalid_token_for_testing",
        "Content-Type": "application/json"
    }
    url = "http://84.247.130.122:8090/api/tasks/5093"
    
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print("ERROR DETAILS:")
        print(f"Type: {type(e)}")
        print(f"Repr: {repr(e)}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
