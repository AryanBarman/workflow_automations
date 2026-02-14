import unittest

# Adjust path to import app modules
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from app.steps.ai_step import AiStep
from app.core.executor_contract import ExecutionContext


class TestAiStepGuardrails(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext(
            workflow_execution_id="test-exec",
            step_execution_id="test-step",
            workflow_id="test-wf",
            step_id="test-step-def",
            trigger_input={}
        )

    def test_min_text_length_guardrail(self):
        step = AiStep(config={
            "provider": "mock",
            "model": "mock-1",
            "prompt_template": "Hello {name}",
            "min_text_length": 200,
        })
        result = step.execute({"name": "World"}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "AI_OUTPUT_INVALID")
        self.assertEqual(result.error.error_type, "permanent")
        print("✅ Guardrail min_text_length: PASSED")

    def test_forbidden_phrase_guardrail(self):
        step = AiStep(config={
            "provider": "mock",
            "model": "mock-1",
            "prompt_template": "Hello {name}",
            "forbidden_phrases": ["mock_response"],
        })
        result = step.execute({"name": "World"}, self.context)

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error.code, "AI_OUTPUT_INVALID")
        self.assertEqual(result.error.error_type, "permanent")
        print("✅ Guardrail forbidden phrase: PASSED")


if __name__ == "__main__":
    unittest.main()
