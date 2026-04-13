import asyncio
import sys
import os
sys.path.append(os.getcwd())
from backend.service.rama import consulta_por_nombre

async def main():
    print("Searching for 'RODRIGUEZ BELENO ILUMINADA' in depto 08 (Atlantico)...")
    res = await consulta_por_nombre("RODRIGUEZ BELENO ILUMINADA", id_depto="08")
    if res and res.get("procesos"):
        p = res["procesos"][0]
        print(f"Keys in a process: {list(p.keys())}")
        print(f"Sample 'numero': {p.get('numero')}")
        print(f"Sample 'id': {p.get('id')}")
    else:
        print("No results found or portal blocked.")

if __name__ == "__main__":
    asyncio.run(main())
