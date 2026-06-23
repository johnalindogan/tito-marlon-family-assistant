from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_message_returns_fallback_reply() -> None:
    response = client.post(
        "/message",
        json={"sender_id": "sender-1", "message": "Kumusta?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert body["memories_saved"] == []
    assert "Tito Marlon" in body["reply"]


def test_message_rejects_blank_text() -> None:
    response = client.post(
        "/message",
        json={"sender_id": "sender-1", "message": "   "},
    )

    assert response.status_code == 422
