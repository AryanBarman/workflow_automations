"""
Unit tests for WorkflowExecution and StepExecution repositories.

Tests cover:
- Execution creation and retrieval
- Immutability constraints
- Status transitions
- Error handling
"""

import pytest
from datetime import datetime

from app.models import (
    Workflow,
    WorkflowExecution,
    WorkflowExecutionStatus,
    StepExecution,
    StepExecutionStatus,
    StepType,
)
from app.repositories import (
    WorkflowRepository,
    WorkflowExecutionRepository,
    StepExecutionRepository,
)
from app.core.exceptions import ImmutabilityViolationError


@pytest.mark.asyncio
class TestWorkflowExecutionRepository:
    """Tests for WorkflowExecutionRepository."""
    
    async def test_create_execution(self, test_db):
        """Test creating a workflow execution."""
        # Create workflow first
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        # Create execution
        exec_repo = WorkflowExecutionRepository(test_db)
        execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual",
            status=WorkflowExecutionStatus.PENDING
        )
        
        assert execution.id is not None
        assert execution.workflow_id == workflow.id
        assert execution.status == WorkflowExecutionStatus.PENDING
        assert execution.trigger_source == "manual"
    
    async def test_update_execution_status(self, test_db):
        """Test updating execution status."""
        # Create workflow and execution
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual"
        )
        
        # Update status
        updated = await exec_repo.update_status(
            execution.id,
            WorkflowExecutionStatus.RUNNING
        )
        
        assert updated.status == WorkflowExecutionStatus.RUNNING
    
    async def test_cannot_update_terminal_execution(self, test_db):
        """Test that terminal executions cannot be modified."""
        # Create workflow and execution
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual",
            status=WorkflowExecutionStatus.SUCCESS
        )
        
        # Try to update terminal execution
        with pytest.raises(ImmutabilityViolationError):
            await exec_repo.update_status(
                execution.id,
                WorkflowExecutionStatus.RUNNING
            )
    
    async def test_get_executions_by_workflow_id(self, test_db):
        """Test retrieving all executions for a workflow."""
        # Create workflow
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        # Create multiple executions
        exec_repo = WorkflowExecutionRepository(test_db)
        for i in range(3):
            await exec_repo.create(
                workflow_id=workflow.id,
                workflow_version=workflow.version,
                trigger_source=f"trigger_{i}"
            )
        
        # Retrieve all executions
        executions = await exec_repo.get_by_workflow_id(workflow.id)
        
        assert len(executions) == 3
    
    async def test_is_terminal_property(self, test_db):
        """Test the is_terminal property."""
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create(
            name="Test Workflow",
            version=1,
            created_by="test_user"
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        
        # Pending is not terminal
        pending = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual",
            status=WorkflowExecutionStatus.PENDING
        )
        assert not pending.is_terminal
        
        # Success is terminal
        success = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual",
            status=WorkflowExecutionStatus.SUCCESS
        )
        assert success.is_terminal


@pytest.mark.asyncio
class TestStepExecutionRepository:
    """Tests for StepExecutionRepository."""
    
    async def test_create_step_execution(self, test_db):
        """Test creating a step execution."""
        # Create workflow with steps
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=[
                {"type": StepType.MANUAL, "config": {}, "order": 1}
            ]
        )
        
        # Create workflow execution
        exec_repo = WorkflowExecutionRepository(test_db)
        workflow_execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual"
        )
        
        # Create step execution
        step_exec_repo = StepExecutionRepository(test_db)
        step_execution = await step_exec_repo.create(
            workflow_execution_id=workflow_execution.id,
            step_id=workflow.steps[0].id,
            input={"data": "test"},
            status=StepExecutionStatus.PENDING
        )
        
        assert step_execution.id is not None
        assert step_execution.status == StepExecutionStatus.PENDING
        assert step_execution.input == {"data": "test"}
    
    async def test_update_step_execution_with_output(self, test_db):
        """Test updating step execution with output."""
        # Setup
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=[{"type": StepType.LOGIC, "config": {}, "order": 1}]
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        workflow_execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual"
        )
        
        step_exec_repo = StepExecutionRepository(test_db)
        step_execution = await step_exec_repo.create(
            workflow_execution_id=workflow_execution.id,
            step_id=workflow.steps[0].id,
            status=StepExecutionStatus.RUNNING
        )
        
        # Update with output
        updated = await step_exec_repo.update_status(
            step_execution.id,
            StepExecutionStatus.SUCCESS,
            output={"result": "completed"}
        )
        
        assert updated.status == StepExecutionStatus.SUCCESS
        assert updated.output == {"result": "completed"}
    
    async def test_cannot_update_terminal_step_execution(self, test_db):
        """Test that terminal step executions cannot be modified."""
        # Setup
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=[{"type": StepType.MANUAL, "config": {}, "order": 1}]
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        workflow_execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual"
        )
        
        step_exec_repo = StepExecutionRepository(test_db)
        step_execution = await step_exec_repo.create(
            workflow_execution_id=workflow_execution.id,
            step_id=workflow.steps[0].id,
            status=StepExecutionStatus.SUCCESS
        )
        
        # Try to update terminal step execution
        with pytest.raises(ImmutabilityViolationError):
            await step_exec_repo.update_status(
                step_execution.id,
                StepExecutionStatus.RUNNING
            )
    
    async def test_get_step_executions_by_workflow_execution(self, test_db):
        """Test retrieving all step executions for a workflow execution."""
        # Setup
        workflow_repo = WorkflowRepository(test_db)
        workflow = await workflow_repo.create_with_steps(
            name="Test Workflow",
            created_by="test_user",
            steps_data=[
                {"type": StepType.MANUAL, "config": {}, "order": 1},
                {"type": StepType.LOGIC, "config": {}, "order": 2},
            ]
        )
        
        exec_repo = WorkflowExecutionRepository(test_db)
        workflow_execution = await exec_repo.create(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_source="manual"
        )
        
        # Create step executions
        step_exec_repo = StepExecutionRepository(test_db)
        for step in workflow.steps:
            await step_exec_repo.create(
                workflow_execution_id=workflow_execution.id,
                step_id=step.id,
                status=StepExecutionStatus.PENDING
            )
        
        # Retrieve all step executions
        step_executions = await step_exec_repo.get_by_workflow_execution_id(
            workflow_execution.id
        )
        
        assert len(step_executions) == 2
