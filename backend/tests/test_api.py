from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_verify_endpoint_accepts_claims():
    response = client.post(
        "/verify",
        json={"claims": [{"claim": "ChatGPT launched in 2018.", "type": "date"}]},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "FALSE"

