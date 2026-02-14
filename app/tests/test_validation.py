
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os

# Adjust path
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from app.executor.linear_executor import LinearExecutor
from app.models import Step, StepType
from app.core.executor_contract import StepResult, StepMetadata
from app.models.step_execution import StepExecutionStatus

class TestValidation(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.executor = LinearExecutor(self.mock_session)
        
    @patch('app.executor.linear_executor.LinearExecutor._instantiate_step')
    def test_input_validation_failure(self, mock_instantiate):
        # Setup: Step with strict input schema (required "value" must be integer)
        step = Step(
            id="test-validation-1",
            type=StepType.LOGIC,
            config={},
            order=1,
            # Schema: {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}
            input_schema={
                "type": "object", 
                "properties": {"value": {"type": "integer"}}, 
                "required": ["value"]
            }
        )
        
        # Mock execution objects
        step_execution = MagicMock()
        workflow = MagicMock()
        workflow_execution = MagicMock()
        
        # Test 1: Invalid Input (String instead of Int)
        print("\n🧪 Testing Input Validation Failure...")
        invalid_input = {"value": "not-an-int"}
        
        # Call _execute_single_step
        result = self.executor._execute_single_step(
            step, step_execution, workflow, workflow_execution, {}, invalid_input
        )
        
        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "VALIDATION_ERROR")
        self.assertEqual(result.error.error_type, "permanent")
        print(f"✅ Input validation caught error: {result.error.message}")

    @patch('app.executor.linear_executor.LinearExecutor._instantiate_step')
    def test_output_validation_failure(self, mock_instantiate):
        # Setup: Step with strict output schema
        step = Step(
            id="test-validation-2",
            type=StepType.LOGIC,
            config={},
            order=1,
            # Schema: Output must contain "processed": True
            output_schema={
                "type": "object", 
                "properties": {"processed": {"type": "boolean", "const": True}}, 
                "required": ["processed"]
            }
        )
        
        # Mock step executor to return invalid output
        mock_step_instance = MagicMock()
        # Returns output missing "processed" field
        mock_step_instance.execute.return_value = StepResult(
            status="success", 
            output={"data": "something"}, 
            metadata=StepMetadata(duration_ms=10, started_at=datetime.utcnow(), finished_at=datetime.utcnow())
        )
        mock_instantiate.return_value = mock_step_instance
        
        step_execution = MagicMock()
        workflow = MagicMock()
        workflow_execution = MagicMock()
        
        print("\n🧪 Testing Output Validation Failure...")
        result = self.executor._execute_single_step(
            step, step_execution, workflow, workflow_execution, {}, {}
        )
        
        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "VALIDATION_ERROR")
        self.assertEqual(result.error.error_type, "permanent")
        print(f"✅ Output validation caught error: {result.error.message}")

    @patch('app.executor.linear_executor.LinearExecutor._instantiate_step')
    def test_validation_success(self, mock_instantiate):
        # Setup: Success case
        step = Step(
            id="test-validation-3",
            type=StepType.LOGIC,
            config={},
            order=1,
            input_schema={"type": "object", "properties": {"val": {"type": "integer"}}},
            output_schema={"type": "object", "properties": {"res": {"type": "string"}}}
        )
        
        mock_step_instance = MagicMock()
        mock_step_instance.execute.return_value = StepResult(
            status="success", 
            output={"res": "ok"}, 
            metadata=StepMetadata(duration_ms=10, started_at=datetime.utcnow(), finished_at=datetime.utcnow())
        )
        mock_instantiate.return_value = mock_step_instance
        
        step_execution = MagicMock()
        workflow = MagicMock()
        workflow_execution = MagicMock()
        
        print("\n🧪 Testing Validation Success...")
        result = self.executor._execute_single_step(
            step, step_execution, workflow, workflow_execution, {}, {"val": 123}
        )
        
        self.assertEqual(result.status, "success")
        print("✅ Validation passed successfully")

if __name__ == '__main__':
    unittest.main()
