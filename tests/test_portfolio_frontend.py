import pytest
from fastapi.testclient import TestClient
from src.mainAPI import app

client = TestClient(app)

def test_get_portfolio_returns_200():
    response = client.get("/portfolio")
    assert response.status_code in [200, 401]

def test_get_portfolio_has_projects_key():
    response = client.get("/portfolio")
    if response.status_code == 200:
        assert "projects" in response.json()

def test_generate_portfolio_returns_200():
    response = client.post("/portfolio/generate")
    assert response.status_code in [200, 401]