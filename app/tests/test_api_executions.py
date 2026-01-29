"""
Test for executions API endpoints - Task 1.1.4 & 1.1.5
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_execution_not_found():
    """Test that GET /api/executions/{id} returns 404 for non-existent execution."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/executions/{fake_uuid}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_execution_logs_not_found():
    """Test that GET /api/executions/{id}/logs returns 404 for non-existent execution."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/executions/{fake_uuid}/logs")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# Note: Tests with database fixtures require async test client
# These tests validate the endpoint contract works correctly
# Integration tests with real data should use async test patterns
