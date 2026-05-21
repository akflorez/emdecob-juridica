import asyncio
from backend.service.publicaciones import consultar_publicaciones_rango

async def main():
    res = await consultar_publicaciones_rango(
        '11001-40-03-024-2024-01403-00', 
        '2026-02-01', 
        'FONDO NACIONAL DEL AHORRO CARLOS LLERAS RESTREPO', 
        'PEDRO ELIAS MORENO GONZALES'
    )
    print(f'Total: {len(res)}')
    for i, r in enumerate(res):
        print(f'--- #{i+1} ---')
        print(f'  tipo: {r.get("tipo","")}')
        print(f'  fecha: {r.get("fecha","")}')
        snippet = str(r.get("snippet",""))[:150]
        print(f'  snippet: {snippet}')
        print(f'  url: {r.get("documento_url","")}')
        print(f'  source_id: {r.get("source_id","")}')

asyncio.run(main())
