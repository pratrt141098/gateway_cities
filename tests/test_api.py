import pytest
from unittest.mock import patch

from backend.app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json == {"ok": True}


def test_cities(client):
    mock_data = [
        {
            "city": "Lowell",
            "city_type": "gateway",
            "year": 2024,
        }
    ]

    with patch(
        "backend.app.data_store.get_cities_master",
        return_value=mock_data,
    ):
        response = client.get("/api/cities")

    assert response.status_code == 200
    assert response.json == mock_data


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": 123},
        {"message": "x" * 2001},
        [],
    ],
)
def test_chat_invalid_input(client, payload):
    response = client.post(
        "/api/chat",
        json=payload,
    )

    assert response.status_code == 400
    assert "error" in response.json


def test_chat_success(client):
    mock_answer = {
        "answer": "Lowell is a Gateway City.",
        "chart": None,
    }

    with patch(
        "backend.app.chat_service.chat",
        return_value=mock_answer,
    ):
        response = client.post(
            "/api/chat",
            json={"message": "Tell me about Lowell"},
        )

    assert response.status_code == 200
    assert response.json == mock_answer


def test_chat_internal_error(client):
    with patch(
        "backend.app.chat_service.chat",
        side_effect=RuntimeError(
            "sensitive internal details"
        ),
    ):
        response = client.post(
            "/api/chat",
            json={"message": "Tell me about Lowell"},
        )

    assert response.status_code == 500
    assert "error" in response.json
    assert (
        "sensitive internal details"
        not in response.get_data(as_text=True)
    )