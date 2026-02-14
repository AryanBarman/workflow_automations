import unittest

# Adjust path to import app modules
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from app.steps.ai_step import AiStep
from app.core.executor_contract import ExecutionContext


class TestAiStep(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext(
            workflow_execution_id="test-exec",
            step_execution_id="test-step",
            workflow_id="test-wf",
            step_id="test-step-def",
            trigger_input={}
        )

    def test_mock_provider_success(self):
        step = AiStep(config={
            "provider": "mock",
            "model": "mock-1",
            "prompt_template": "Hello {name}",
        })
        result = step.execute({"name": "World"}, self.context)

        self.assertEqual(result.status, "success")
        self.assertIn("text", result.output)
        self.assertTrue(result.output["text"].startswith("MOCK_RESPONSE: Hello World"))
        self.assertEqual(result.output["_ai_meta"]["provider"], "mock")
        print("? Mock provider success: PASSED")

    def test_missing_prompt_fails(self):
        step = AiStep(config={"provider": "mock"})
        result = step.execute({"name": "World"}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "PROMPT_MISSING")
        self.assertEqual(result.error.error_type, "permanent")
        print("? Missing prompt failure: PASSED")

    def test_prompt_template_missing_key_fails(self):
        step = AiStep(config={"provider": "mock", "prompt_template": "Hello {name}"})
        result = step.execute({"wrong": "key"}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "PROMPT_FORMAT_ERROR")
        self.assertEqual(result.error.error_type, "permanent")
        print("? Prompt template key failure: PASSED")


if __name__ == '__main__':
    unittest.main()
