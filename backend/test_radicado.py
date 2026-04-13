import asyncio
import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.rama import consulta_por_radicado
from backend.main import extract_items

async def test():
    radicado = "68547400300520250083300"
    print(f"🔍 Probando radicado: {radicado}")
    r = await consulta_por_radicado(radicado)
    items = extract_items(r)
    if not items:
        print("❌ No se encontraron ítems")
        return
    
    p = items[0]
    print(f"✅ Ítem encontrado")
    print(f"   - idProceso: {p.get('idProceso')}")
    print(f"   - IdProceso: {p.get('IdProceso')}")
    print(f"   - id_proceso: {p.get('id_proceso')}")
    print(f"   - llaveProceso: {p.get('llaveProceso')}")
    print(f"   - despacho: {p.get('despacho')}")

if __name__ == "__main__":
    asyncio.run(test())
