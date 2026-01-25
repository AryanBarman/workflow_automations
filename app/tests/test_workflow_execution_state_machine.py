"""
Unit tests for WorkflowExecution state machine - Phase 0, Slice 0.3, Task 0.3.1

Tests validate:
1. All valid state transitions work correctly
2. Invalid transitions are rejected
3. Terminal states are immutable
4. Timestamps are set correctly
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.core.exceptions import InvalidStateTransitionError


class TestWorkflowExecutionValidTransitions:
    """Test all valid state transitions."""
    
    def test_pending_to_running(self):
        """Test transition from PENDING to RUNNING."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="manual"
        )
        
        # Transition should succeed
        execution.transition_to(WorkflowExecutionStatus.RUNNING)
        
        assert execution.status == WorkflowExecutionStatus.RUNNING
        assert execution.started_at is not None
        assert execution.finished_at is None
    
    def test_running_to_success(self):
        """Test transition from RUNNING to SUCCESS."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(WorkflowExecutionStatus.SUCCESS)
        
        assert execution.status == WorkflowExecutionStatus.SUCCESS
        assert execution.finished_at is not None
        assert execution.is_terminal is True
    
    def test_running_to_failed(self):
        """Test transition from RUNNING to FAILED."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(WorkflowExecutionStatus.FAILED)
        
        assert execution.status == WorkflowExecutionStatus.FAILED
        assert execution.finished_at is not None
        assert execution.is_terminal is True
    
    def test_running_to_cancelled(self):
        """Test transition from RUNNING to CANCELLED."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(WorkflowExecutionStatus.CANCELLED)
        
        assert execution.status == WorkflowExecutionStatus.CANCELLED
        assert execution.finished_at is not None
        assert execution.is_terminal is True


class TestWorkflowExecutionInvalidTransitions:
    """Test that invalid transitions are rejected."""
    
    def test_pending_to_success_rejected(self):
        """Test that PENDING cannot jump directly to SUCCESS."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="manual"
        )
        
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            execution.transition_to(WorkflowExecutionStatus.SUCCESS)
        
        assert "pending" in str(exc_info.value).lower()
        assert "success" in str(exc_info.value).lower()
        # Status should remain unchanged
        assert execution.status == WorkflowExecutionStatus.PENDING
    
    def test_pending_to_failed_rejected(self):
        """Test that PENDING cannot jump directly to FAILED."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="manual"
        )
        
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(WorkflowExecutionStatus.FAILED)
        
        assert execution.status == WorkflowExecutionStatus.PENDING
    
    def test_running_to_pending_rejected(self):
        """Test that RUNNING cannot go back to PENDING."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(WorkflowExecutionStatus.PENDING)
        
        assert execution.status == WorkflowExecutionStatus.RUNNING


class TestWorkflowExecutionTerminalStateImmutability:
    """Test that terminal states cannot be modified."""
    
    def test_success_is_immutable(self):
        """Test that SUCCESS state cannot be changed."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.SUCCESS,
            trigger_source="manual",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from SUCCESS to RUNNING
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            execution.transition_to(WorkflowExecutionStatus.RUNNING)
        
        assert "success" in str(exc_info.value).lower()
        # Status should remain unchanged
        assert execution.status == WorkflowExecutionStatus.SUCCESS
    
    def test_failed_is_immutable(self):
        """Test that FAILED state cannot be changed."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.FAILED,
            trigger_source="manual",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from FAILED to RUNNING
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(WorkflowExecutionStatus.RUNNING)
        
        assert execution.status == WorkflowExecutionStatus.FAILED
    
    def test_cancelled_is_immutable(self):
        """Test that CANCELLED state cannot be changed."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.CANCELLED,
            trigger_source="manual",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from CANCELLED to SUCCESS
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(WorkflowExecutionStatus.SUCCESS)
        
        assert execution.status == WorkflowExecutionStatus.CANCELLED


class TestWorkflowExecutionTimestamps:
    """Test that timestamps are set correctly during transitions."""
    
    def test_started_at_set_when_running(self):
        """Test that started_at is set when transitioning to RUNNING."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="manual"
        )
        
        assert execution.started_at is None
        
        execution.transition_to(WorkflowExecutionStatus.RUNNING)
        
        assert execution.started_at is not None
        assert isinstance(execution.started_at, datetime)
    
    def test_finished_at_set_on_success(self):
        """Test that finished_at is set when transitioning to SUCCESS."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        assert execution.finished_at is None
        
        execution.transition_to(WorkflowExecutionStatus.SUCCESS)
        
        assert execution.finished_at is not None
        assert isinstance(execution.finished_at, datetime)
    
    def test_finished_at_set_on_failed(self):
        """Test that finished_at is set when transitioning to FAILED."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        execution.transition_to(WorkflowExecutionStatus.FAILED)
        
        assert execution.finished_at is not None
    
    def test_finished_at_set_on_cancelled(self):
        """Test that finished_at is set when transitioning to CANCELLED."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual",
            started_at=datetime.utcnow()
        )
        
        execution.transition_to(WorkflowExecutionStatus.CANCELLED)
        
        assert execution.finished_at is not None


class TestWorkflowExecutionIsTerminalProperty:
    """Test the is_terminal property."""
    
    def test_pending_not_terminal(self):
        """Test that PENDING is not terminal."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="manual"
        )
        
        assert execution.is_terminal is False
    
    def test_running_not_terminal(self):
        """Test that RUNNING is not terminal."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.RUNNING,
            trigger_source="manual"
        )
        
        assert execution.is_terminal is False
    
    def test_success_is_terminal(self):
        """Test that SUCCESS is terminal."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.SUCCESS,
            trigger_source="manual"
        )
        
        assert execution.is_terminal is True
    
    def test_failed_is_terminal(self):
        """Test that FAILED is terminal."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.FAILED,
            trigger_source="manual"
        )
        
        assert execution.is_terminal is True
    
    def test_cancelled_is_terminal(self):
        """Test that CANCELLED is terminal."""
        execution = WorkflowExecution(
            workflow_id=uuid4(),
            workflow_version=1,
            status=WorkflowExecutionStatus.CANCELLED,
            trigger_source="manual"
        )
        
        assert execution.is_terminal is True
