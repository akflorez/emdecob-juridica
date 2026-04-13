import httpx
import asyncio
import json

BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

async def test_endpoint(client, method, path, data=None, params=None):
    print(f"\n--- Testing {method} {path} ---")
    try:
        if method == "GET":
            r = await client.get(f"{BASE_URL}{path}", params=params)
        else:
            r = await client.post(f"{BASE_URL}{path}", json=data, params=params)
        
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            res = r.json()
            print(f"✅ Success! Data: {str(res)[:300]}...")
            return True
        else:
            print(f"❌ Failed: {r.text[:200]}")
    except Exception as e:
        print(f"💥 Error: {e}")
    return False

async def main():
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, verify=False) as client:
        # Test 1: Radicado 68547400300520250083300
        print("Searching radicado 68547400300520250083300...")
        await test_endpoint(client, "GET", "/Proceso/NumeroRadicacion", params={"numero": "68547400300520250083300", "SoloActivos": "false"})
        await test_endpoint(client, "GET", "/Procesos/Consulta/NumeroRadicacion", params={"numero": "68547400300520250083300", "SoloActivos": "false"})

        # Test 2: Search by Name (RICARDO) - GET variations
        print("\nSearching by name 'RICARDO' (GET)...")
        name_params = {"nombre": "RICARDO", "soloActivos": "false", "pagina": 1, "tipoPersona": 1}
        await test_endpoint(client, "GET", "/Proceso/Consulta/NombreRazonSocial", params=name_params)
        await test_endpoint(client, "GET", "/Procesos/Consulta/NombreRazonSocial", params=name_params)

        # Test 3: Search by Name (RICARDO) - POST variations
        print("\nSearching by name 'RICARDO' (POST)...")
        name_data = {"nombre": "RICARDO", "soloActivos": False, "pagina": 1, "tipoPersona": 1}
        await test_endpoint(client, "POST", "/Proceso/Consulta/NombreRazonSocial", data=name_data)
        await test_endpoint(client, "POST", "/Procesos/Consulta/NombreRazonSocial", data=name_data)

if __name__ == "__main__":
    asyncio.run(main())
