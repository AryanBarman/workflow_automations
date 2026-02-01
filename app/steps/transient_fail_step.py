"""
TransientFailStep - Phase 1 step type for testing retry logic

A step that fails transiently N times, then succeeds.
Used to test retry behavior in Workflow 1A.

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


class TransientFailStep:
    """
    TransientFailStep - A step that fails N times, then succeeds.
    
    This step is used to test retry logic in workflows.
    It tracks failure count in the step config and fails until
    the configured number of attempts is reached.
    
    Config:
        fail_count: Number of times to fail before succeeding (default: 2)
    
    Use cases:
        - Testing retry logic (Workflow 1A)
        - Validating transient error handling
        - Simulating network failures that eventually succeed
    
    Example:
        step = TransientFailStep()
        # First call: fails with transient error
        # Second call: fails with transient error
        # Third call: succeeds
    """
    
    def __init__(self):
        self.attempt_count = 0
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        """
        Execute the transient fail step.
        
        Fails with transient error for first N attempts, then succeeds.
        
        Args:
            input: The input data
            context: Execution context with IDs and metadata
            
        Returns:
            StepResult with status="failure" for first N attempts,
            then status="success"
        """
        started_at = datetime.utcnow()
        
        # Increment attempt counter
        self.attempt_count += 1
        
        # Get fail_count from step config (default: 2)
        # Note: In real implementation, this would come from step.config
        # For now, we hardcode it to fail 2 times
        fail_count = 2
        
        if self.attempt_count <= fail_count:
            # Fail with transient error
            input_summary = str(input)[:100] if input else "None"
            error_message = (
                f"TransientFailStep failed (attempt {self.attempt_count}/{fail_count + 1}). "
                f"This is a simulated transient failure. "
                f"Step ID: {context.step_id}, "
                f"Workflow Execution ID: {context.workflow_execution_id}, "
                f"Timestamp: {started_at.isoformat()}, "
                f"Input: {input_summary}"
            )
            
            error = StepError(
                code="TRANSIENT_FAILURE",
                message=error_message,
                retryable=True,
                error_type="transient"  # This is a transient error
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
        else:
            # Succeed after N failures
            output = {
                "result": "success",
                "attempts": self.attempt_count,
                "message": f"Succeeded after {fail_count} transient failures"
            }
            
            finished_at = datetime.utcnow()
            duration_ms = int((finished_at - started_at).total_seconds() * 1000)
            
            metadata = StepMetadata(
                duration_ms=duration_ms,
                started_at=started_at,
                finished_at=finished_at
            )
            
            return StepResult(
                status="success",
                output=output,
                metadata=metadata
            )
