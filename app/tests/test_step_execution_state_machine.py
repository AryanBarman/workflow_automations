"""
Unit tests for StepExecution state machine - Phase 0, Slice 0.3, Task 0.3.2

Tests validate:
1. All valid state transitions work correctly
2. Invalid transitions are rejected
3. Terminal states (SUCCESS, FAILED, SKIPPED) are immutable
4. Timestamps are set correctly
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.step_execution import StepExecution, StepExecutionStatus
from app.core.exceptions import InvalidStateTransitionError


class TestStepExecutionValidTransitions:
    """Test all valid state transitions."""
    
    def test_pending_to_running(self):
        """Test transition from PENDING to RUNNING."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        # Transition should succeed
        execution.transition_to(StepExecutionStatus.RUNNING)
        
        assert execution.status == StepExecutionStatus.RUNNING
        assert execution.started_at is not None
        assert execution.finished_at is None
    
    def test_running_to_success(self):
        """Test transition from RUNNING to SUCCESS."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(StepExecutionStatus.SUCCESS)
        
        assert execution.status == StepExecutionStatus.SUCCESS
        assert execution.finished_at is not None
        assert execution.is_terminal is True
    
    def test_running_to_failed(self):
        """Test transition from RUNNING to FAILED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(StepExecutionStatus.FAILED)
        
        assert execution.status == StepExecutionStatus.FAILED
        assert execution.finished_at is not None
        assert execution.is_terminal is True
    
    def test_running_to_skipped(self):
        """Test transition from RUNNING to SKIPPED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Transition should succeed
        execution.transition_to(StepExecutionStatus.SKIPPED)
        
        assert execution.status == StepExecutionStatus.SKIPPED
        assert execution.finished_at is not None
        assert execution.is_terminal is True


class TestStepExecutionInvalidTransitions:
    """Test that invalid transitions are rejected."""
    
    def test_pending_to_success_rejected(self):
        """Test that PENDING cannot jump directly to SUCCESS."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            execution.transition_to(StepExecutionStatus.SUCCESS)
        
        assert "pending" in str(exc_info.value).lower()
        assert "success" in str(exc_info.value).lower()
        # Status should remain unchanged
        assert execution.status == StepExecutionStatus.PENDING
    
    def test_pending_to_failed_rejected(self):
        """Test that PENDING cannot jump directly to FAILED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(StepExecutionStatus.FAILED)
        
        assert execution.status == StepExecutionStatus.PENDING
    
    def test_pending_to_skipped_rejected(self):
        """Test that PENDING cannot jump directly to SKIPPED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(StepExecutionStatus.SKIPPED)
        
        assert execution.status == StepExecutionStatus.PENDING
    
    def test_running_to_pending_rejected(self):
        """Test that RUNNING cannot go back to PENDING."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(StepExecutionStatus.PENDING)
        
        assert execution.status == StepExecutionStatus.RUNNING


class TestStepExecutionTerminalStateImmutability:
    """Test that terminal states cannot be modified."""
    
    def test_success_is_immutable(self):
        """Test that SUCCESS state cannot be changed."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.SUCCESS,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from SUCCESS to RUNNING
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            execution.transition_to(StepExecutionStatus.RUNNING)
        
        assert "success" in str(exc_info.value).lower()
        # Status should remain unchanged
        assert execution.status == StepExecutionStatus.SUCCESS
    
    def test_failed_is_immutable(self):
        """Test that FAILED state cannot be changed."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.FAILED,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from FAILED to RUNNING
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(StepExecutionStatus.RUNNING)
        
        assert execution.status == StepExecutionStatus.FAILED
    
    def test_skipped_is_immutable(self):
        """Test that SKIPPED state cannot be changed."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.SKIPPED,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        # Try to transition from SKIPPED to SUCCESS
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(StepExecutionStatus.SUCCESS)
        
        assert execution.status == StepExecutionStatus.SKIPPED


class TestStepExecutionTimestamps:
    """Test that timestamps are set correctly during transitions."""
    
    def test_started_at_set_when_running(self):
        """Test that started_at is set when transitioning to RUNNING."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        assert execution.started_at is None
        
        execution.transition_to(StepExecutionStatus.RUNNING)
        
        assert execution.started_at is not None
        assert isinstance(execution.started_at, datetime)
    
    def test_finished_at_set_on_success(self):
        """Test that finished_at is set when transitioning to SUCCESS."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        assert execution.finished_at is None
        
        execution.transition_to(StepExecutionStatus.SUCCESS)
        
        assert execution.finished_at is not None
        assert isinstance(execution.finished_at, datetime)
    
    def test_finished_at_set_on_failed(self):
        """Test that finished_at is set when transitioning to FAILED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        execution.transition_to(StepExecutionStatus.FAILED)
        
        assert execution.finished_at is not None
    
    def test_finished_at_set_on_skipped(self):
        """Test that finished_at is set when transitioning to SKIPPED."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        execution.transition_to(StepExecutionStatus.SKIPPED)
        
        assert execution.finished_at is not None


class TestStepExecutionIsTerminalProperty:
    """Test the is_terminal property."""
    
    def test_pending_not_terminal(self):
        """Test that PENDING is not terminal."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.PENDING
        )
        
        assert execution.is_terminal is False
    
    def test_running_not_terminal(self):
        """Test that RUNNING is not terminal."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.RUNNING
        )
        
        assert execution.is_terminal is False
    
    def test_success_is_terminal(self):
        """Test that SUCCESS is terminal."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.SUCCESS
        )
        
        assert execution.is_terminal is True
    
    def test_failed_is_terminal(self):
        """Test that FAILED is terminal."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.FAILED
        )
        
        assert execution.is_terminal is True
    
    def test_skipped_is_terminal(self):
        """Test that SKIPPED is terminal."""
        execution = StepExecution(
            workflow_execution_id=uuid4(),
            step_id=uuid4(),
            status=StepExecutionStatus.SKIPPED
        )
        
        assert execution.is_terminal is True
