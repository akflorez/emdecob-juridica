import asyncio
import httpx
import json

async def test_endpoint():
    radicado = "68547400300520240014000" # Example radicado
    base_url = "http://localhost:8000" # Update if different
    
    print(f"Testing refresh endpoint for {radicado}...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{base_url}/cases/{radicado}/refresh-publicaciones")
            if resp.status_code == 200:
                data = resp.json()
                print("Success! Data received:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Failed: {resp.status_code}")
                print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: Backend must be running for this to work
    # asyncio.run(test_endpoint())
    print("Test script created. Run this when backend is active.")
