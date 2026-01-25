"""
PersistStep - Phase 0 canonical step type

A step with side effects that simulates data persistence.
For Phase 0, this just returns success without actual persistence.

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


class PersistStep:
    """
    PersistStep - A side-effect step that simulates persistence.
    
    This step represents operations with side effects like:
    - Writing to database
    - Saving to file system
    - Sending notifications
    - External API calls (write operations)
    
    For Phase 0, we simulate persistence without actually writing anywhere.
    This proves the contract works for side-effect steps.
    
    Example:
        step = PersistStep()
        result = step.execute({"data": "to_save"}, context)
        # result.output == {"persisted": True, "record_count": 1}
    """
    
    def execute(self, input: Any, context: ExecutionContext) -> StepResult:
        """
        Execute the persist step - simulate data persistence.
        
        Args:
            input: The data to "persist" (any JSON-serializable type)
            context: Execution context with IDs and metadata
            
        Returns:
            StepResult with status="success" and persistence confirmation
        """
        started_at = datetime.utcnow()
        
        # Simulate persistence (no actual I/O for Phase 0)
        # In real implementation, this would:
        # - Write to database
        # - Save to file
        # - Call external API
        # etc.
        
        # For now, just return success with metadata
        output = {
            "persisted": True,
            "persisted_at": started_at.isoformat(),
            "step_execution_id": str(context.step_execution_id),
            "record_count": 1 if input else 0,
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
