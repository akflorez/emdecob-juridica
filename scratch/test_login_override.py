import sqlalchemy as sa
import urllib.request
import json
import urllib.error

DB_URL = 'postgresql://emdecob:emdecob2026@84.247.130.122:5432/juricob'
engine = sa.create_engine(DB_URL)

temp_hash = "$pbkdf2-sha256$29000$ek.ptXbOuXfO.V.LMWasFQ$wk1K3G98dz9PD1cqeK9oVosKTFTGwl75VN/fRnRtHLU"

with engine.connect() as conn:
    # Set the hash
    conn.execute(sa.text("UPDATE users SET hashed_password = :h WHERE username='admin'"), {"h": temp_hash})
    conn.commit()

data = json.dumps({'username': 'admin', 'password': 'Emdecob2026*'}).encode()
req = urllib.request.Request('http://84.247.130.122:8090/api/auth/login', data=data, headers={'Content-Type': 'application/json'})

try:
    resp = urllib.request.urlopen(req)
    print("SUCCESS", resp.read().decode())
except urllib.error.HTTPError as e:
    print("FAILED", e.code, e.read().decode())
