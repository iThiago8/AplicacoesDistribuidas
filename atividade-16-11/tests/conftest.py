import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend_fastapi import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "admin123")
    monkeypatch.setenv("SEED_DEMO", "1")
    return create_app(f"sqlite:///{tmp_path / 'teste.db'}")


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def admin(client):
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def headers(admin):
    return {"Authorization": f"Bearer {admin['access_token']}"}
