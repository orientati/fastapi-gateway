import os
import sys
import traceback

os.environ['GATEWAY_ENVIRONMENT'] = 'testing'

try:
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    res = client.get('/openapi.json')
    if res.status_code != 200:
        raise Exception(f"Status: {res.status_code}\nResponse: {res.text}")
    print("Success")
except Exception:
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        f.write(traceback.format_exc())
    print("See error_log.txt")
