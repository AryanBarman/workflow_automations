
import unittest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime

# Adjust path
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from app.executor.linear_executor import LinearExecutor
from app.models import Step, StepType, Workflow, WorkflowExecution
from app.core.executor_contract import StepResult, StepMetadata

# Define a Slow Step Executor
class SlowStepExecutor:
    def __init__(self, config=None):
        self.config = config or {}
        
    def execute(self, input, context):
        sleep_time = self.config.get("sleep", 0)
        print(f"😴 SlowStep sleeping for {sleep_time}s...")
        time.sleep(sleep_time)
        print("⏰ SlowStep woke up!")
        
        started_at = datetime.utcnow()
        finished_at = datetime.utcnow()
        metadata = StepMetadata(duration_ms=int(sleep_time*1000), started_at=started_at, finished_at=finished_at)
        return StepResult(status="success", output="done", metadata=metadata)

class TestStepTimeout(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.executor = LinearExecutor(self.mock_session)
        
    @patch('app.executor.linear_executor.LinearExecutor._instantiate_step')
    def test_step_timeout_enforcement(self, mock_instantiate):
        # Setup: Step configured to sleep 2s, but timeout is 1s
        step = Step(
            id="test-id",
            type=StepType.LOGIC,
            config={"sleep": 2},
            timeout_seconds=1,
            order=1
        )
        
        # Mock instantiation to return our SlowStep
        mock_instantiate.return_value = SlowStepExecutor(config=step.config)
        
        # Mock execution context creation and logging calls
        # We need to mock _execute_single_step's dependencies?
        # Actually, let's test _execute_single_step directly if possible, 
        # but it does DB commits.
        
        # Better: Test _execute_single_step with mocks for DB
        step_execution = MagicMock()
        workflow = MagicMock()
        workflow_execution = MagicMock()
        
        # Execute
        print("\n🧪 Testing Timeout (Expected: Failure)...")
        start = time.time()
        result = self.executor._execute_single_step(
            step, step_execution, workflow, workflow_execution, {}, {}
        )
        duration = time.time() - start
        
        # Assertions
        print(f"⏱️ execution duration: {duration:.2f}s")
        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "TIMEOUT")
        self.assertEqual(result.error.error_type, "transient")
        self.assertTrue(result.error.retryable)
        self.assertLess(duration, 1.5) # Should be close to 1s, definitely not 2s
        print("✅ Timeout test passed!")

    @patch('app.executor.linear_executor.LinearExecutor._instantiate_step')
    def test_step_within_timeout(self, mock_instantiate):
        # Setup: Step sleeps 0.5s, timeout 2s
        step = Step(
            id="test-id-2",
            type=StepType.LOGIC,
            config={"sleep": 0.5},
            timeout_seconds=2,
            order=1
        )
        
        mock_instantiate.return_value = SlowStepExecutor(config=step.config)
        step_execution = MagicMock()
        workflow = MagicMock()
        workflow_execution = MagicMock()
        
        print("\n🧪 Testing Success (Expected: Success)...")
        result = self.executor._execute_single_step(
            step, step_execution, workflow, workflow_execution, {}, {}
        )
        
        self.assertEqual(result.status, "success")
        print("✅ Within-timeout test passed!")

if __name__ == '__main__':
    unittest.main()
