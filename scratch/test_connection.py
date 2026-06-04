import os
import sys
import asyncio
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.service.publicaciones import consultar_publicaciones_rango

async def test():
    radicado = "11001400302120250005200"
    fecha = "2025-04-04"
    print(f"Testing publications search for {radicado} on {fecha}...")
    try:
        res = await consultar_publicaciones_rango(
            radicado, 
            fecha, 
            "FONDO NACIONAL DEL AHORRO CARLOS LLERAS RESTREPO", 
            "LINA TRASLAVIÑA SOLANO"
        )
        print(f"Result count: {len(res)}")
        for r in res:
            print(f"- {r.get('fecha')} | {r.get('descripcion')}")
            print(f"  URL: {r.get('documento_url')}")
    except Exception as e:
        print(f"Exception caught in test:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
