import os
import sys

import pytest
from fastapi.testclient import TestClient

from src.mainAPI import app

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

client = TestClient(app)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def signup(email: str, password: str = "password123") -> dict:
    """Attempt signup and return the full response dict."""
    response = client.post("/auth/signup", json={
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": password
    })
    return response


def login(email: str, password: str = "password123") -> dict:
    """Attempt login and return the full response."""
    return client.post("/auth/login", json={
        "email": email,
        "password": password
    })


def get_token(email: str, password: str = "password123") -> str:
    """Register or login and return the token."""
    response = signup(email, password)
    if response.status_code == 400:
        response = login(email, password)
    assert response.status_code == 200
    return response.json()["token"]


# ──────────────────────────────────────────────
# Signup Tests
# ──────────────────────────────────────────────

def test_signup_success():
    """Valid signup returns user info and token."""
    response = signup("signup_success@example.com")
    # May already exist from a previous run
    if response.status_code == 400:
        assert "already registered" in response.json()["detail"]
        return

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "signup_success@example.com"
    assert "id" in data["user"]
    assert "first_name" in data["user"]
    assert "last_name" in data["user"]


def test_signup_duplicate_email():
    """Signing up with an already registered email returns 400."""
    email = "duplicate@example.com"
    signup(email)  # First signup — may already exist, doesn't matter
    response = signup(email)  # Second signup should always fail
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signup_password_too_short():
    """Password under 6 characters returns 400."""
    response = signup("shortpass@example.com", password="abc")
    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()


def test_signup_missing_fields():
    """Missing required fields returns 422."""
    response = client.post("/auth/signup", json={
        "email": "missingfields@example.com",
        "password": "password123"
        # missing first_name and last_name
    })
    assert response.status_code == 422


def test_signup_invalid_email():
    """Invalid email format returns 422."""
    response = client.post("/auth/signup", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "not-an-email",
        "password": "password123"
    })
    assert response.status_code == 422


# ──────────────────────────────────────────────
# Login Tests
# ──────────────────────────────────────────────

def test_login_success():
    """Valid login returns user info and token."""
    email = "login_success@example.com"
    get_token(email)  # Ensure user exists

    response = login(email)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == email


def test_login_wrong_password():
    """Wrong password returns 401."""
    email = "wrong_pass@example.com"
    get_token(email)  # Ensure user exists

    response = login(email, password="wrongpassword")
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user():
    """Login with an email that was never registered returns 401."""
    response = login("ghost_user_xyz@example.com")
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_invalid_email_format():
    """Login with malformed email returns 422."""
    response = client.post("/auth/login", json={
        "email": "not-valid",
        "password": "password123"
    })
    assert response.status_code == 422


def test_login_missing_fields():
    """Login with missing password returns 422."""
    response = client.post("/auth/login", json={
        "email": "someuser@example.com"
    })
    assert response.status_code == 422


# ──────────────────────────────────────────────
# /auth/me Tests
# ──────────────────────────────────────────────

def test_get_me_success():
    """Authenticated user can retrieve their profile."""
    email = "get_me@example.com"
    token = get_token(email)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "first_name" in data
    assert "last_name" in data
    assert "education_count" in data
    assert "work_history_count" in data
    assert "project_count" in data


def test_get_me_no_token():
    """Request to /auth/me without a token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token():
    """Request to /auth/me with a bad token returns 401."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer totallyinvalidtoken"}
    )
    assert response.status_code == 401


# ──────────────────────────────────────────────
# /auth/guest/projects/count Tests
# ──────────────────────────────────────────────

def test_guest_project_count_no_auth():
    """Guest project count is accessible without authentication."""
    response = client.get("/auth/guest/projects/count")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "message" in data
    assert isinstance(data["count"], int)
    assert data["count"] >= 0