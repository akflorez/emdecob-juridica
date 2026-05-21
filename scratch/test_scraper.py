
import asyncio
from backend.service.publicaciones import consultar_publicaciones_rango

async def main():
    print("Scraping...")
    # Buscamos desde 2024 para ver qué trae
    res = await consultar_publicaciones_rango("11001400302420240140300", "2024-01-01", "FONDO NACIONAL DEL AHORRO", "PEDRO ELIAS MORENO")
    print(f"Resultados encontrados: {len(res)}")
    for r in res:
        print(f"Fecha: {r['fecha']} | Tipo: {r['tipo']}")
        print(f"Snippet: {r['snippet'][:100]}...")
        print(f"URL: {r['documento_url']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
