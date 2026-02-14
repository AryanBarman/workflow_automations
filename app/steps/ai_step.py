"""
AiStep - Phase 3 AI dependency step.

This step executes a prompt against a configured provider and returns
structured output. It follows the StepExecutor contract and treats
AI as an external dependency.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
import os
import requests

from app.core.executor_contract import (
    StepExecutor,
    StepResult,
    StepError,
    StepMetadata,
    ExecutionContext,
)


class AiStep:
    """
    AiStep - Executes a prompt via an AI provider.

    Config:
        provider: "mock" | "openai" (default: "mock")
        model: Provider model id (default: "mock-1")
        prompt: Static prompt string
        prompt_template: Python format string to build prompt from input
        prompt_id: Optional prompt identifier
        prompt_version: Optional prompt version
        temperature: Optional model temperature
        max_tokens: Optional token cap
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        started_at = datetime.utcnow()

        provider = self.config.get("provider", "mock")
        model = self.config.get("model", "mock-1")
        prompt_id = self.config.get("prompt_id")
        prompt_version = self.config.get("prompt_version")

        prompt_text_result = self._build_prompt(input)
        if isinstance(prompt_text_result, StepResult):
            return prompt_text_result
        prompt_text = prompt_text_result

        try:
            if provider == "mock":
                output_text = f"MOCK_RESPONSE: {prompt_text}"
                usage = {"prompt_tokens": len(prompt_text.split()), "completion_tokens": len(output_text.split())}
                guardrail_result = self._evaluate_output(output_text, started_at)
                if guardrail_result is not None:
                    return guardrail_result
                return self._success(started_at, output_text, model, provider, prompt_id, prompt_version, usage)

            if provider == "openai":
                return self._execute_openai(
                    started_at=started_at,
                    prompt_text=prompt_text,
                    model=model,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            return self._fail(
                started_at,
                code="AI_CONFIG_ERROR",
                message=f"Unknown AI provider: {provider}",
                error_type="permanent",
            )

        except Exception as exc:
            return self._fail(
                started_at,
                code="AI_ERROR",
                message=f"AI execution error: {exc}",
                error_type="transient",
            )

    def _build_prompt(self, input: Any) -> str | StepResult:
        if "prompt" in self.config and self.config.get("prompt"):
            return str(self.config.get("prompt"))

        template = self.config.get("prompt_template")
        if not template:
            return self._fail(
                datetime.utcnow(),
                code="PROMPT_MISSING",
                message="AI step requires 'prompt' or 'prompt_template'",
                error_type="permanent",
            )

        if not isinstance(input, dict):
            return self._fail(
                datetime.utcnow(),
                code="PROMPT_INPUT_ERROR",
                message="prompt_template requires dict input",
                error_type="permanent",
            )

        try:
            return str(template).format(**input)
        except KeyError as exc:
            return self._fail(
                datetime.utcnow(),
                code="PROMPT_FORMAT_ERROR",
                message=f"Missing template key: {exc}",
                error_type="permanent",
            )

    def _execute_openai(
        self,
        *,
        started_at: datetime,
        prompt_text: str,
        model: str,
        prompt_id: str | None,
        prompt_version: str | None,
    ) -> StepResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return self._fail(
                started_at,
                code="AI_CONFIG_ERROR",
                message="OPENAI_API_KEY is not set",
                error_type="permanent",
            )

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
        }

        temperature = self.config.get("temperature")
        if temperature is not None:
            payload["temperature"] = temperature

        max_tokens = self.config.get("max_tokens")
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.config.get("timeout", 30),
        )

        if response.status_code >= 400:
            error_type = "transient" if response.status_code in (429, 500, 502, 503, 504) else "permanent"
            return self._fail(
                started_at,
                code="AI_HTTP_ERROR",
                message=f"OpenAI HTTP {response.status_code}: {response.text[:200]}",
                error_type=error_type,
            )

        data = response.json()
        output_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage") or {}

        guardrail_result = self._evaluate_output(output_text, started_at)
        if guardrail_result is not None:
            return guardrail_result

        return self._success(started_at, output_text, model, "openai", prompt_id, prompt_version, usage)

    def _success(
        self,
        started_at: datetime,
        output_text: str,
        model: str,
        provider: str,
        prompt_id: str | None,
        prompt_version: str | None,
        usage: Dict[str, Any],
    ) -> StepResult:
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)

        output = {
            "text": output_text,
            "_ai_meta": {
                "provider": provider,
                "model": model,
                "prompt_id": prompt_id,
                "prompt_version": prompt_version,
                "usage": usage,
            },
        }

        return StepResult(status="success", output=output, metadata=metadata)

    def _evaluate_output(self, output_text: str, started_at: datetime) -> StepResult | None:
        min_length = self.config.get("min_text_length")
        if min_length is not None:
            try:
                min_length = int(min_length)
            except (TypeError, ValueError):
                min_length = None
        if min_length is not None and len(output_text.strip()) < min_length:
            return self._fail(
                started_at,
                code="AI_OUTPUT_INVALID",
                message=f"Output too short (min {min_length} chars)",
                error_type="permanent",
            )

        forbidden_phrases = self.config.get("forbidden_phrases") or []
        if isinstance(forbidden_phrases, list):
            lower_text = output_text.lower()
            for phrase in forbidden_phrases:
                if isinstance(phrase, str) and phrase.lower() in lower_text:
                    return self._fail(
                        started_at,
                        code="AI_OUTPUT_INVALID",
                        message=f"Output contains forbidden phrase: {phrase}",
                        error_type="permanent",
                    )

        return None

    def _fail(self, started_at: datetime, code: str, message: str, error_type: str) -> StepResult:
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        metadata = StepMetadata(duration_ms=duration_ms, started_at=started_at, finished_at=finished_at)
        error = StepError(
            code=code,
            message=message,
            retryable=(error_type == "transient"),
            error_type=error_type,
        )
        return StepResult(status="failure", error=error, metadata=metadata)
