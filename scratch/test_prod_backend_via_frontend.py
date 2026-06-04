import httpx
import asyncio

async def main():
    url = "http://84.247.130.122:8090/api/docs"
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(url)
            print(f"GET {url} -> status={resp.status_code} | length={len(resp.text)}")
            if resp.status_code != 200:
                print(f"Response body: {resp.text[:400]}")
    except Exception as e:
        print(f"Error connecting: {e}")

if __name__ == "__main__":
    asyncio.run(main())
