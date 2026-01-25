"""
FailStep - Phase 0 canonical step type

A step that always fails - used for testing failure paths.

Contract: StepExecutor
"""

from datetime import datetime
from typing import Any

from app.core.executor_contract import (
    StepExecutor,
    StepResult,
    StepError,
    StepMetadata,
    ExecutionContext,
)


class FailStep:
    """
    FailStep - A step that always fails.
    
    This step is used to test failure handling in workflows.
    It always returns a failure result with an error.
    
    Use cases:
    - Testing workflow failure paths (Workflow 0B)
    - Validating error propagation
    - Testing retry logic (Phase 1)
    - Simulating external failures
    
    Example:
        step = FailStep()
        result = step.execute({"data": "any"}, context)
        # result.status == "failure"
        # result.error.code == "FORCED_FAILURE"
    """
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        """
        Execute the fail step - always returns failure.
        
        Args:
            input: The input data (ignored, step always fails)
            context: Execution context with IDs and metadata
            
        Returns:
            StepResult with status="failure" and error details
        """
        started_at = datetime.utcnow()
        
        # This step always fails
        error = StepError(
            code="FORCED_FAILURE",
            message="This step is designed to fail for testing purposes",
            retryable=False  # Forced failures are not retryable
        )
        
        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        
        metadata = StepMetadata(
            duration_ms=duration_ms,
            started_at=started_at,
            finished_at=finished_at
        )
        
        return StepResult(
            status="failure",
            error=error,
            metadata=metadata
        )
