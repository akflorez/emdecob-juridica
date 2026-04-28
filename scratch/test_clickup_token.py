
import httpx
import asyncio

TOKEN = "pk_26368479_4ISVQXGZFEQZZGYOA1IOV32BUIE41TGX"

async def test():
    headers = {"Authorization": TOKEN}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.clickup.com/api/v2/user", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Data: {r.text}")

if __name__ == "__main__":
    asyncio.run(test())
