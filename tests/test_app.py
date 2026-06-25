from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoDatabaseSession:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    monkeypatch.setattr("app.service.database.session_scope", lambda: NoDatabaseSession())
    monkeypatch.setattr("app.service.extract_memories", lambda message: [])
    monkeypatch.setattr(
        "app.service.generate_reply",
        lambda sender_id, message, image_urls, recent_chat, memory: (
            "Hi, ako si Tito Marlon. Naka-receive ako ng message mo. "
            "Inaayos pa ang full AI memory ko, pero nandito ako para tumulong."
        ),
    )


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


def test_message_accepts_image_without_text() -> None:
    response = client.post(
        "/message",
        json={
            "sender_id": "sender-1",
            "image_urls": ["https://example.com/photo.jpg"],
        },
    )

    assert response.status_code == 200
    assert "reply" in response.json()


def test_system_prompt_allows_photos() -> None:
    from app.prompts import SYSTEM_PROMPT

    assert "Photos are allowed" in SYSTEM_PROMPT
    assert "Do not claim photos are forbidden" in SYSTEM_PROMPT


def test_user_content_includes_image_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import ai

    monkeypatch.setattr(ai, "_download_image_data_url", lambda image_url: None)

    content = ai._user_content("Ano ito?", ["https://example.com/photo.jpg"])

    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "Ano ito?"}
    assert content[1] == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/photo.jpg"},
    }
