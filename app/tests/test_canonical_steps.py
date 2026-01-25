"""
Unit tests for Canonical Phase 0 Step Types - Task 0.3.6

Tests validate:
1. All steps implement the StepExecutor contract correctly
2. Each step produces proper StepResult
3. Metadata is populated correctly
4. Step-specific behavior works as expected
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.steps import InputStep, TransformStep, PersistStep, FailStep
from app.core.executor_contract import StepResult, ExecutionContext


class TestInputStep:
    """Test InputStep - pass-through behavior."""
    
    def test_input_step_passes_through_dict(self):
        """Test that InputStep returns input as output for dict."""
        step = InputStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = {"user_id": "123", "action": "process"}
        result = step.execute(input_data, context)
        
        assert isinstance(result, StepResult)
        assert result.status == "success"
        assert result.output == input_data
        assert result.error is None
        assert result.metadata is not None
        assert result.metadata.duration_ms >= 0
    
    def test_input_step_passes_through_string(self):
        """Test that InputStep returns input as output for string."""
        step = InputStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = "test string"
        result = step.execute(input_data, context)
        
        assert result.status == "success"
        assert result.output == input_data
    
    def test_input_step_metadata_populated(self):
        """Test that InputStep populates metadata correctly."""
        step = InputStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        result = step.execute({"data": "test"}, context)
        
        assert result.metadata is not None
        assert isinstance(result.metadata.duration_ms, int)
        assert isinstance(result.metadata.started_at, datetime)
        assert isinstance(result.metadata.finished_at, datetime)
        assert result.metadata.finished_at >= result.metadata.started_at


class TestTransformStep:
    """Test TransformStep - transformation behavior."""
    
    def test_transform_step_adds_metadata_to_dict(self):
        """Test that TransformStep adds processing metadata to dict input."""
        step = TransformStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = {"original": "data"}
        result = step.execute(input_data, context)
        
        assert result.status == "success"
        assert result.output is not None
        assert "original" in result.output
        assert result.output["original"] == "data"
        assert "processed" in result.output
        assert result.output["processed"] is True
        assert "processed_at" in result.output
        assert "workflow_execution_id" in result.output
    
    def test_transform_step_wraps_non_dict_input(self):
        """Test that TransformStep wraps non-dict input."""
        step = TransformStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = "string input"
        result = step.execute(input_data, context)
        
        assert result.status == "success"
        assert "original_input" in result.output
        assert result.output["original_input"] == "string input"
        assert "processed" in result.output
        assert result.output["processed"] is True
    
    def test_transform_step_is_deterministic(self):
        """Test that TransformStep produces consistent output structure."""
        step = TransformStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = {"test": "data"}
        result1 = step.execute(input_data, context)
        result2 = step.execute(input_data, context)
        
        # Both should have same keys (though timestamps will differ)
        assert set(result1.output.keys()) == set(result2.output.keys())
        assert result1.output["processed"] == result2.output["processed"]


class TestPersistStep:
    """Test PersistStep - persistence simulation."""
    
    def test_persist_step_returns_success(self):
        """Test that PersistStep returns success."""
        step = PersistStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = {"data": "to_persist"}
        result = step.execute(input_data, context)
        
        assert result.status == "success"
        assert result.error is None
    
    def test_persist_step_output_structure(self):
        """Test that PersistStep returns expected output structure."""
        step = PersistStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        input_data = {"data": "to_persist"}
        result = step.execute(input_data, context)
        
        assert "persisted" in result.output
        assert result.output["persisted"] is True
        assert "persisted_at" in result.output
        assert "step_execution_id" in result.output
        assert "record_count" in result.output
        assert result.output["record_count"] == 1
    
    def test_persist_step_handles_empty_input(self):
        """Test that PersistStep handles empty input."""
        step = PersistStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        result = step.execute(None, context)
        
        assert result.status == "success"
        assert result.output["record_count"] == 0


class TestFailStep:
    """Test FailStep - forced failure behavior."""
    
    def test_fail_step_always_fails(self):
        """Test that FailStep always returns failure."""
        step = FailStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        result = step.execute({"any": "data"}, context)
        
        assert result.status == "failure"
        assert result.output is None
        assert result.error is not None
    
    def test_fail_step_error_structure(self):
        """Test that FailStep returns proper error structure."""
        step = FailStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        result = step.execute({}, context)
        
        assert result.error.code == "FORCED_FAILURE"
        assert "testing purposes" in result.error.message.lower()
        assert result.error.retryable is False
    
    def test_fail_step_ignores_input(self):
        """Test that FailStep fails regardless of input."""
        step = FailStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        # Try with different inputs - all should fail
        result1 = step.execute({"data": "test"}, context)
        result2 = step.execute(None, context)
        result3 = step.execute("string", context)
        
        assert result1.status == "failure"
        assert result2.status == "failure"
        assert result3.status == "failure"


class TestContractCompliance:
    """Test that all steps comply with the StepExecutor contract."""
    
    def test_all_steps_return_step_result(self):
        """Test that all steps return StepResult instances."""
        steps = [InputStep(), TransformStep(), PersistStep(), FailStep()]
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        for step in steps:
            result = step.execute({"test": "data"}, context)
            assert isinstance(result, StepResult)
    
    def test_all_steps_populate_metadata(self):
        """Test that all steps populate metadata."""
        steps = [InputStep(), TransformStep(), PersistStep(), FailStep()]
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        for step in steps:
            result = step.execute({"test": "data"}, context)
            assert result.metadata is not None
            assert result.metadata.duration_ms >= 0
            assert result.metadata.started_at is not None
            assert result.metadata.finished_at is not None
    
    def test_success_steps_have_output_no_error(self):
        """Test that successful steps have output and no error."""
        success_steps = [InputStep(), TransformStep(), PersistStep()]
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        for step in success_steps:
            result = step.execute({"test": "data"}, context)
            assert result.status == "success"
            assert result.output is not None
            assert result.error is None
    
    def test_fail_step_has_error_no_output(self):
        """Test that FailStep has error and no output."""
        step = FailStep()
        context = ExecutionContext(
            workflow_execution_id=uuid4(),
            step_execution_id=uuid4(),
            workflow_id=uuid4(),
            step_id=uuid4(),
            trigger_input={}
        )
        
        result = step.execute({"test": "data"}, context)
        assert result.status == "failure"
        assert result.output is None
        assert result.error is not None
