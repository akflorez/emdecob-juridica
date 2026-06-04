import asyncio
import sys
from backend.service.publicaciones import consultar_publicaciones_rango

async def main():
    radicado = "63401408900220240026600"
    demandante = "FONDO NACIONAL DEL AHORRO S.A."
    demandado = "DUVAN SANTOS SAAVEDRA"
    date_str = "2024-01-01"
    
    print(f"Starting test for {radicado}", flush=True)
    res = await consultar_publicaciones_rango(radicado, date_str, demandante, demandado)
    print(f"Results: {len(res)} found", flush=True)
    for r in res:
        print(f"Found validated: {r['documento_url']}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
