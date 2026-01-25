"""
TransformStep - Phase 0 canonical step type

A pure logic step that transforms input data.
No side effects, deterministic output.

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


class TransformStep:
    """
    TransformStep - A pure logic transformation step.
    
    This step applies a transformation to input data and returns the result.
    For Phase 0, we use simple hardcoded transformations.
    
    Characteristics:
    - Pure function (no side effects)
    - Deterministic (same input → same output)
    - Stateless
    
    Phase 0 transformation: Adds a "processed" field to the input
    
    Example:
        step = TransformStep()
        result = step.execute({"data": "value"}, context)
        # result.output == {"data": "value", "processed": True, "timestamp": "..."}
    """
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        """
        Execute the transform step - apply transformation to input.
        
        Args:
            input: The input data (any JSON-serializable type)
            context: Execution context with IDs and metadata
            
        Returns:
            StepResult with status="success" and transformed output
        """
        started_at = datetime.utcnow()
        
        # Phase 0 transformation: Add processing metadata
        # In later phases, this could be configurable
        if isinstance(input, dict):
            output = {
                **input,
                "processed": True,
                "processed_at": started_at.isoformat(),
                "workflow_execution_id": str(context.workflow_execution_id),
            }
        else:
            # For non-dict inputs, wrap in a dict
            output = {
                "original_input": input,
                "processed": True,
                "processed_at": started_at.isoformat(),
                "workflow_execution_id": str(context.workflow_execution_id),
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
