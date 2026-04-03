from api.routes import auth
from api.routes.auth import decode_token


def test_register_creates_web_only_account_when_telegram_id_is_missing(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "web-only@example.com",
            "password": "secret123",
            "name": "Web User",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "web-only@example.com"
    assert payload["has_telegram_link"] is False
    assert payload["account_type"] == "web-only"
    assert payload["telegram_id"] < 0
    assert payload["token_type"] == "bearer"
    assert decode_token(payload["access_token"])["sub"] == "web-only@example.com"


def test_register_rejects_duplicate_email(client):
    first = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "secret123",
            "name": "First User",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "secret123",
            "name": "Second User",
        },
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "Ya existe una cuenta con ese email"


def test_login_returns_access_token_and_admin_flag(client, temp_db):
    temp_db.create_user_if_not_exists(321, "Admin User")
    temp_db.create_web_user(321, "admin@example.com", auth.get_password_hash("adminpass"))
    temp_db._execute("UPDATE users SET is_admin = 1 WHERE telegram_id = ?", (321,))

    response = client.post(
        "/auth/token",
        data={"username": "admin@example.com", "password": "adminpass"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["telegram_id"] == 321
    assert payload["is_admin"] is True


def test_password_reset_flow_updates_password(client, temp_db, monkeypatch):
    temp_db.create_user_if_not_exists(777, "Reset User")
    temp_db.create_web_user(777, "reset@example.com", auth.get_password_hash("oldpass"))
    monkeypatch.setattr(auth.secrets, "token_urlsafe", lambda _: "fixed-reset-token-long-enough")
    monkeypatch.setattr(auth, "_send_password_reset_email", lambda email, url: None)

    response = client.post("/auth/password-reset/request", json={"email": "reset@example.com"})

    assert response.status_code == 200
    assert "te enviamos un enlace" in response.json()["message"]

    confirm = client.post(
        "/auth/password-reset/confirm",
        json={"token": "fixed-reset-token-long-enough", "password": "newpass123"},
    )

    assert confirm.status_code == 200
    assert confirm.json()["message"] == "Password actualizada correctamente"

    login = client.post(
        "/auth/token",
        data={"username": "reset@example.com", "password": "newpass123"},
    )

    assert login.status_code == 200


def test_password_reset_confirm_rejects_invalid_token(client):
    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": "invalid-token-long-enough", "password": "newpass123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El enlace de recuperacion es invalido o ya expiró"
