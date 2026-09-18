from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_welcome():
    response=client.get("/welcome")

    assert response.status_code == 401
