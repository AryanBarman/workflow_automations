"""
Unit tests for Workflow and Step repositories.

Tests cover:
- Entity creation and retrieval
- Relationship loading
- Transaction safety
- Workflow versioning
"""

import pytest
from uuid import uuid4

from app.models import Workflow, Step, StepType
from app.repositories import WorkflowRepository, StepRepository


@pytest.mark.asyncio
class TestWorkflowRepository:
    """Tests for WorkflowRepository."""
    
    async def test_create_workflow(self, test_db):
        """Test creating a workflow."""
        repo = WorkflowRepository(test_db)
        
        workflow = await repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
        assert workflow.version == 1
        assert workflow.created_by == "test_user"
        assert workflow.created_at is not None
    
    async def test_get_workflow_by_id(self, test_db):
        """Test retrieving workflow by ID."""
        repo = WorkflowRepository(test_db)
        
        # Create workflow
        workflow = await repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        # Retrieve it
        retrieved = await repo.get_by_id(workflow.id)
        
        assert retrieved is not None
        assert retrieved.id == workflow.id
        assert retrieved.name == workflow.name
    
    async def test_get_workflow_by_name_and_version(self, test_db):
        """Test retrieving workflow by name and version."""
        repo = WorkflowRepository(test_db)
        
        # Create workflow
        await repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        # Retrieve by name and version
        retrieved = await repo.get_by_name_and_version("Test Workflow", 1)
        
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"
        assert retrieved.version == 1
    
    async def test_create_workflow_with_steps(self, test_db):
        """Test creating workflow with steps in a transaction."""
        repo = WorkflowRepository(test_db)
        
        steps_data = [
            {"type": StepType.MANUAL, "config": {"action": "review"}, "order": 1},
            {"type": StepType.LOGIC, "config": {"function": "validate"}, "order": 2},
            {"type": StepType.API, "config": {"url": "https://api.example.com"}, "order": 3},
        ]
        
        workflow = await repo.create_with_steps(
            name="Multi-Step Workflow",
            created_by="test_user",
            steps_data=steps_data
        )
        
        assert workflow.id is not None
        assert len(workflow.steps) == 3
        assert workflow.steps[0].type == StepType.MANUAL
        assert workflow.steps[0].order == 1
        assert workflow.steps[1].type == StepType.LOGIC
        assert workflow.steps[2].type == StepType.API
    
    async def test_get_workflow_with_steps(self, test_db):
        """Test eager loading of workflow steps."""
        repo = WorkflowRepository(test_db)
        
        # Create workflow with steps
        steps_data = [
            {"type": StepType.MANUAL, "config": {}, "order": 1},
            {"type": StepType.LOGIC, "config": {}, "order": 2},
        ]
        
        workflow = await repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=steps_data
        )
        
        # Retrieve with steps
        retrieved = await repo.get_by_id_with_steps(workflow.id)
        
        assert retrieved is not None
        assert len(retrieved.steps) == 2
        assert retrieved.steps[0].order == 1
        assert retrieved.steps[1].order == 2


@pytest.mark.asyncio
class TestStepRepository:
    """Tests for StepRepository."""
    
    async def test_get_steps_by_workflow_id(self, test_db):
        """Test retrieving all steps for a workflow."""
        workflow_repo = WorkflowRepository(test_db)
        step_repo = StepRepository(test_db)
        
        # Create workflow with steps
        steps_data = [
            {"type": StepType.MANUAL, "config": {}, "order": 1},
            {"type": StepType.LOGIC, "config": {}, "order": 2},
            {"type": StepType.API, "config": {}, "order": 3},
        ]
        
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=steps_data
        )
        
        # Get steps
        steps = await step_repo.get_by_workflow_id(workflow.id)
        
        assert len(steps) == 3
        assert steps[0].order == 1
        assert steps[1].order == 2
        assert steps[2].order == 3
    
    async def test_step_config_jsonb(self, test_db):
        """Test that step config is stored as JSONB."""
        workflow_repo = WorkflowRepository(test_db)
        
        complex_config = {
            "url": "https://api.example.com",
            "method": "POST",
            "headers": {"Authorization": "Bearer token"},
            "body": {"key": "value"},
            "timeout": 30
        }
        
        steps_data = [
            {"type": StepType.API, "config": complex_config, "order": 1}
        ]
        
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=steps_data
        )
        
        # Verify config is preserved
        assert workflow.steps[0].config == complex_config
        assert workflow.steps[0].config["headers"]["Authorization"] == "Bearer token"
