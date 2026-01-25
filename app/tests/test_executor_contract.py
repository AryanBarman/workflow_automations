"""
Unit tests for Step Executor Contract - Phase 0, Slice 0.2

Tests validate:
1. StepResult structure compliance
2. Success result shape
3. Failure result shape
4. Invalid result rejection
5. ExecutionContext structure

These tests ensure the contract is well-defined and enforceable.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.core.executor_contract import (
    StepExecutor,
    StepResult,
    StepError,
    StepMetadata,
    ExecutionContext,
)


# ============================================================================
# Task 0.2.0.4: Unit Tests for Contract Compliance
# ============================================================================

class TestStepResult:
    """Test StepResult structure and validation."""
    
    def test_success_result_shape(self):
        """A success result must have status='success' and output."""
        metadata = StepMetadata(
            duration_ms=100,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        result = StepResult(
            status="success",
            output={"result": "completed"},
            metadata=metadata
        )
        
        assert result.status == "success"
        assert result.output == {"result": "completed"}
        assert result.error is None
        assert result.metadata == metadata
    
    def test_failure_result_shape(self):
        """A failure result must have status='failure' and error."""
        error = StepError(
            code="VALIDATION_FAILED",
            message="Input validation failed",
            retryable=False
        )
        
        metadata = StepMetadata(
            duration_ms=50,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        
        result = StepResult(
            status="failure",
            error=error,
            metadata=metadata
        )
        
        assert result.status == "failure"
        assert result.output is None
        assert result.error == error
        assert result.metadata == metadata
    
    def test_invalid_status_rejected(self):
        """StepResult must reject invalid status values."""
        with pytest.raises(ValueError, match="Invalid status"):
            StepResult(
                status="pending",  # Invalid status
                output={"data": "test"}
            )
    
    def test_success_cannot_have_error(self):
        """A success result cannot have an error."""
        error = StepError(code="ERROR", message="Test", retryable=False)
        
        with pytest.raises(ValueError, match="Success result cannot have an error"):
            StepResult(
                status="success",
                output={"data": "test"},
                error=error  # This is invalid
            )
    
    def test_failure_must_have_error(self):
        """A failure result must have an error."""
        with pytest.raises(ValueError, match="Failure result must have an error"):
            StepResult(
                status="failure",
                output=None,
                error=None  # This is invalid
            )


class TestStepError:
    """Test StepError structure."""
    
    def test_error_with_retryable_true(self):
        """Test error marked as retryable."""
        error = StepError(
            code="TIMEOUT",
            message="Request timed out",
            retryable=True
        )
        
        assert error.code == "TIMEOUT"
        assert error.message == "Request timed out"
        assert error.retryable is True
    
    def test_error_default_not_retryable(self):
        """Test error defaults to not retryable (conservative)."""
        error = StepError(
            code="INVALID_INPUT",
            message="Input is malformed"
        )
        
        assert error.retryable is False


class TestStepMetadata:
    """Test StepMetadata structure."""
    
    def test_metadata_structure(self):
        """Test metadata contains required timing information."""
        started = datetime.utcnow()
        finished = datetime.utcnow()
        
        metadata = StepMetadata(
            duration_ms=150,
            started_at=started,
            finished_at=finished
        )
        
        assert metadata.duration_ms == 150
        assert metadata.started_at == started
        assert metadata.finished_at == finished


class TestExecutionContext:
    """Test ExecutionContext structure."""
    
    def test_context_structure(self):
        """Test context contains all required execution identifiers."""
        workflow_exec_id = uuid4()
        step_exec_id = uuid4()
        workflow_id = uuid4()
        step_id = uuid4()
        trigger_input = {"user_id": "123", "action": "process"}
        
        context = ExecutionContext(
            workflow_execution_id=workflow_exec_id,
            step_execution_id=step_exec_id,
            workflow_id=workflow_id,
            step_id=step_id,
            trigger_input=trigger_input
        )
        
        assert context.workflow_execution_id == workflow_exec_id
        assert context.step_execution_id == step_exec_id
        assert context.workflow_id == workflow_id
        assert context.step_id == step_id
        assert context.trigger_input == trigger_input


class TestStepExecutorContract:
    """Test that the StepExecutor contract can be implemented correctly."""
    
    def test_simple_step_implementation(self):
        """Test that a simple step can implement the contract."""
        
        class SimplePassThroughStep:
            """A minimal step that just passes input through."""
            
            def execute(self, input: any, context: ExecutionContext) -> StepResult:
                metadata = StepMetadata(
                    duration_ms=10,
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow()
                )
                
                return StepResult(
                    status="success",
                    output=input,
                    metadata=metadata
                )
        
        # Create a step instance
        step = SimplePassThroughStep()
        
        # Create execution context
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={"original": "data"}
        )
        
        # Execute the step
        result = step.execute({"test": "data"}, context)
        
        # Verify the result conforms to the contract
        assert isinstance(result, StepResult)
        assert result.status == "success"
        assert result.output == {"test": "data"}
        assert result.error is None
    
    def test_failing_step_implementation(self):
        """Test that a step can properly return a failure result."""
        
        class FailingStep:
            """A step that always fails."""
            
            def execute(self, input: any, context: ExecutionContext) -> StepResult:
                metadata = StepMetadata(
                    duration_ms=5,
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow()
                )
                
                error = StepError(
                    code="FORCED_FAILURE",
                    message="This step is designed to fail",
                    retryable=False
                )
                
                return StepResult(
                    status="failure",
                    error=error,
                    metadata=metadata
                )
        
        # Create a step instance
        step = FailingStep()
        
        # Create execution context
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        # Execute the step
        result = step.execute({}, context)
        
        # Verify the result conforms to the contract
        assert isinstance(result, StepResult)
        assert result.status == "failure"
        assert result.output is None
        assert result.error is not None
        assert result.error.code == "FORCED_FAILURE"
