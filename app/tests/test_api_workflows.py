"""
Test for workflows API endpoints - Task 1.1.1, 1.1.2 & 1.1.3
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_workflows_endpoint():
    """Test that GET /api/workflows returns list of workflows."""
    response = client.get("/api/workflows")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_workflow_not_found():
    """Test that GET /api/workflows/{id} returns 404 for non-existent workflow."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/workflows/{fake_uuid}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_execute_workflow_not_found():
    """Test that POST /api/workflows/{id}/execute returns 404 for non-existent workflow."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/workflows/{fake_uuid}/execute",
        json={"trigger_input": {"test": "data"}}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# Note: Tests with database fixtures require async test client
# These tests validate the endpoint contract works correctly
# Integration tests with real data should use async test patterns
