import httpx
import asyncio
import json

BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

async def fetch_mappings():
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, verify=False) as client:
        endpoints = [
            "/Entidad/Departamentos",
            "/Entidad/Especialidades",
            "/Entidad/TipoPersona",
        ]
        mappings = {}
        for ep in endpoints:
            print(f"Fetching {ep}...")
            try:
                r = await client.get(f"{BASE_URL}{ep}")
                if r.status_code == 200:
                    mappings[ep] = r.json()
                    print(f"✅ Found {len(mappings[ep])} items for {ep}")
                else:
                    print(f"❌ Failed {ep}: {r.status_code}")
            except Exception as e:
                print(f"💥 Error {ep}: {e}")
        
        with open("rama_mappings.json", "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        print("Mappings saved to rama_mappings.json")

if __name__ == "__main__":
    asyncio.run(fetch_mappings())
