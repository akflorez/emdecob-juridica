import os
import sys
import json
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())
from backend.main import app

def main():
    print("Initializing TestClient...")
    client = TestClient(app)
    
    radicado = "11001400300720250052200"
    
    # 1. Fetch events to populate DB
    print(f"1. Fetching case events for {radicado} from Rama Judicial...")
    events_resp = client.get(f"/cases/{radicado}/events", timeout=120.0)
    print(f"   Events status code: {events_resp.status_code}")
    if events_resp.status_code == 200:
        events = events_resp.json()
        print(f"   Successfully fetched {len(events)} events.")
    else:
        print(f"   Failed to fetch events: {events_resp.text}")
        return
        
    # 2. Call debug endpoint
    payload = {
        "radicado": radicado,
        "force": True
    }
    
    print(f"\n2. Sending POST request to /publicaciones/debug for radicado {radicado}...")
    response = client.post("/publicaciones/debug", json=payload, timeout=180.0)
    
    print(f"\nResponse status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\n=== DEBUG RESPONSE ===")
        print(json.dumps(data, indent=2))
    else:
        print(f"Failed with response: {response.text}")

if __name__ == "__main__":
    main()
