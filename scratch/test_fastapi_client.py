import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Login endpoint test
payload = {"username": "akflorez", "password": "Emdecob2026*"}
response = client.post("/auth/login", json=payload)
print(response.status_code, response.json())
