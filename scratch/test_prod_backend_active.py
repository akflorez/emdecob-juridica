import httpx
import asyncio

async def test_endpoint(url):
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            resp = await client.get(url)
            print(f"GET {url} -> status={resp.status_code} | text={resp.text[:200]}")
    except Exception as e:
        print(f"GET {url} -> Failed: {e}")

async def main():
    # Let's try potential ports on the production server 84.247.130.122
    urls = [
        "http://84.247.130.122:8081/",
        "http://84.247.130.122:8081/api",
        "http://84.247.130.122:8081/docs",
        "http://84.247.130.122:8090/",
        "http://84.247.130.122:8000/",
        "http://84.247.130.122:8000/docs",
    ]
    for url in urls:
        await test_endpoint(url)

if __name__ == "__main__":
    asyncio.run(main())
