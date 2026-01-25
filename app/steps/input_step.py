"""
InputStep - Phase 0 canonical step type

A pass-through step that returns its input as output.
This represents manual input or data that flows through unchanged.

Contract: StepExecutor
"""

from datetime import datetime
from typing import Any

from app.core.executor_contract import (
    StepExecutor,
    StepResult,
    StepMetadata,
    ExecutionContext,
)


class InputStep:
    """
    InputStep - A manual/pass-through step.
    
    This step simply returns its input as output without modification.
    It represents:
    - Manual user input
    - Data that flows through unchanged
    - Starting point for workflows
    
    Example:
        step = InputStep()
        result = step.execute({"user_id": "123"}, context)
        # result.output == {"user_id": "123"}
    """
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        """
        Execute the input step - pass input through as output.
        
        Args:
            input: The input data (any JSON-serializable type)
            context: Execution context with IDs and metadata
            
        Returns:
            StepResult with status="success" and output=input
        """
        started_at = datetime.utcnow()
        
        # Pass-through: input becomes output
        output = input
        
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
