"""
Test for workflows API endpoint - Task 1.1.1
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


def test_list_workflows_with_data(db_session, workflow_0a_happy_path):
    """Test that workflows have correct schema when data exists."""
    # Workflow 0A is created by the fixture
    response = client.get("/api/workflows")
    
    workflows = response.json()
    assert len(workflows) >= 1  # At least workflow 0A exists
    
    # Check first workflow has correct schema
    workflow = workflows[0]
    assert "id" in workflow
    assert "name" in workflow
    assert "version" in workflow
    assert "created_at" in workflow
