
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Adjust path to import app modules
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from app.steps.http_step import HttpStep
from app.core.executor_contract import ExecutionContext

class TestHttpStepFailures(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext(
            workflow_execution_id="test-exec",
            step_execution_id="test-step",
            workflow_id="test-wf",
            step_id="test-step-def",
            trigger_input={}
        )

    @patch('app.steps.http_step.requests.request')
    def test_500_server_error_is_transient(self, mock_request):
        # Simulate 500 Internal Server Error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        step = HttpStep(config={"url": "http://test.com"})
        result = step.execute({}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.error_type, "transient")
        self.assertTrue(result.error.retryable)
        print("\n✅ Test 500 Error -> Transient: PASSED")

    @patch('app.steps.http_step.requests.request')
    def test_404_not_found_is_permanent(self, mock_request):
        # Simulate 404 Not Found
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        step = HttpStep(config={"url": "http://test.com"})
        result = step.execute({}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.error_type, "permanent")
        self.assertFalse(result.error.retryable)
        print("✅ Test 404 Error -> Permanent: PASSED")

    @patch('app.steps.http_step.requests.request')
    def test_network_exception_is_transient(self, mock_request):
        # Simulate Network Exception
        mock_request.side_effect = Exception("Connection refused")

        step = HttpStep(config={"url": "http://test.com"})
        result = step.execute({}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.error_type, "transient")
        self.assertTrue(result.error.retryable)
        print("✅ Test Network Exception -> Transient: PASSED")

if __name__ == '__main__':
    unittest.main()
