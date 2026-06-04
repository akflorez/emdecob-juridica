import os
import sys
import json
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())
from backend.main import app

def main():
    client = TestClient(app)
    radicado = "11001400300720250052200"
    
    print(f"Sending GET request to /cases/{radicado}/publicaciones...")
    response = client.get(f"/cases/{radicado}/publicaciones")
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total items returned: {len(data.get('items', []))}")
        for idx, item in enumerate(data.get('items', [])):
            print(f"  [{idx+1}] ID={item['id']} | Fecha Pub={item['fecha_publicacion']} | Desc={item['descripcion'][:40]}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    main()
