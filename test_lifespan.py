import asyncio
from backend.main import lifespan, app

async def run_lifespan():
    async with lifespan(app):
        print("Lifespan executed.")

if __name__ == "__main__":
    asyncio.run(run_lifespan())
