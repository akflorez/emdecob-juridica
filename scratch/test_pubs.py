
import asyncio
import httpx
from backend.service.publicaciones import consultar_publicaciones

async def test():
    # Use a real radicado that likely has publications
    # I'll use one from the logs or just a random one if I can find it.
    radicado = "11001310301020220034600" # Example radicado
    print(f"Testing publications for: {radicado}")
    results = await consultar_publicaciones(radicado)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- {r['tipo']}: {r['documento_url']}")

if __name__ == "__main__":
    asyncio.run(test())
