import os
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Let's see if we can hit the endpoint without auth, it should return 401
resp = client.get("/api/admin/companies")
print(resp.status_code, resp.text)
