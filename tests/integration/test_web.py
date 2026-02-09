import pytest
from fastapi.testclient import TestClient
from app.web import app
from app.monitor import monitor
import os

client = TestClient(app)

def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dispatcher Console" in response.text

def test_api_stats_unauthorized():
    response = client.get("/api/stats")
    assert response.status_code == 401

def test_token_login():
    # Note: WEB_PASSWORD defaults to "admin" if not set in .env
    # For testing, we can use the default or set it
    from app.config import AppConfig
    password = AppConfig.WEB_PASSWORD
    
    response = client.post(
        "/token",
        data={"username": "admin", "password": password}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_api_stats_authorized():
    from app.config import AppConfig
    password = AppConfig.WEB_PASSWORD
    
    # Get token
    login_res = client.post(
        "/token",
        data={"username": "admin", "password": password}
    )
    token = login_res.json()["access_token"]
    
    # Update monitor state
    monitor.update_stats(cycles_completed=5, messages_processed=100)
    
    response = client.get(
        "/api/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cycles_completed"] == 5
    assert data["messages_processed"] == 100
