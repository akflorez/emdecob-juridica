import httpx
import asyncio
import json

BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

async def test_search():
    name = "RICARDO"
    paths = [
        "/Proceso/Consulta/NombreRazonSocial",
        "/Procesos/Consulta/NombreRazonSocial",
        "/Proceso/NombreRazonSocial",
    ]
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, verify=False) as client:
        for path in paths:
            print(f"Testing {path}...")
            params = {
                "nombre": name,
                "soloActivos": "false",
                "pagina": 1,
                "tipoPersona": 1
            }
            try:
                r = await client.get(f"{BASE_URL}{path}", params=params)
                print(f"Status: {r.status_code}")
                if r.status_code == 200:
                    data = r.json()
                    print(f"Success! Data snippet: {str(data)[:500]}")
                    return
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
