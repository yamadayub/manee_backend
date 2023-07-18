import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app, google_oauth_client

client = TestClient(app)

# ダミーのユーザー情報
dummy_user_info = {
    "id": "1234567890",
    "email": "test@example.com",
    "verified_email": True,
    "name": "Test User",
    "picture": "https://example.com/avatar.png",
}

# google_oauth_client.fetch_tokenのモック
google_oauth_client.fetch_token = MagicMock(
    return_value={"access_token": "dummy_access_token"})

# google_oauth_client.getのモック
google_oauth_client.get = MagicMock(
    return_value=MagicMock(json=lambda: dummy_user_info))


def test_user_registration():
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://example.com/avatar.png",
        "google_id": "1234567890"
    }
    response = client.post("/user/register", json=data)
    assert response.status_code == 200
    assert response.json()["email"] == data["email"]


def test_user_authentication():
    # 仮のGoogle認証コード
    google_auth_code = "4/0AY0e-g6a9mYRWtQN_GDmT1xiWwC0ZuJ7Il0GkOuV7Thq4Xo0V_ktvJ1MvfYVPhg-1zGZsA"

    response = client.get(f"/auth/google/callback?code={google_auth_code}")
    assert response.status_code == 200
