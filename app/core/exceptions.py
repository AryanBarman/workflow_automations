"""
Custom exceptions for the application.
Provides domain-specific error types for better error handling.
"""


class WorkflowExecutionError(Exception):
    """Base exception for workflow execution errors."""
    pass


class EntityNotFoundError(Exception):
    """Raised when a requested entity does not exist."""
    
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class InvalidStateTransitionError(WorkflowExecutionError):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition from {from_state} to {to_state}"
        )


class ImmutabilityViolationError(WorkflowExecutionError):
    """Raised when attempting to modify immutable execution history."""
    
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"Cannot modify {entity_type} {entity_id}: execution history is immutable"
        )
