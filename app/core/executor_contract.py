"""
Step Executor Contract - Phase 0, Slice 0.2

This module defines the foundational contract that ALL step types must conform to.

Key Principles:
1. The executor NEVER inspects step.type - it only calls execute()
2. Steps are STATELESS - all state lives in ExecutionContext or StepExecution
3. The contract signature NEVER changes - future phases extend, never modify
4. Every execution produces a StepResult - no exceptions escape the contract

This contract enables:
- The executor to remain simple and boring
- Step types to evolve independently
- New step types to be added without changing the executor
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


# ============================================================================
# Task 0.2.0.1: StepExecutor Interface
# ============================================================================

class StepExecutor(Protocol):
    """
    The core execution contract that all step types must implement.
    
    This is a Protocol (structural subtyping) rather than an ABC to allow
    flexibility in implementation while maintaining type safety.
    
    Contract:
        execute(input, context) → StepResult
    
    The executor:
    - Does NOT know about step internals
    - Does NOT inspect step.type
    - Only calls execute() and trusts the contract
    
    Example:
        class MyCustomStep:
            def execute(self, input: Any, context: ExecutionContext) -> StepResult:
                # Implementation here
                return StepResult(status="success", output={"result": "done"})
    """
    
    def execute(self, input: Any, context: "ExecutionContext") -> "StepResult":
        """
        Execute the step with the given input and context.
        
        Args:
            input: The input data for this step (can be any JSON-serializable type)
            context: Runtime execution context containing metadata and IDs
            
        Returns:
            StepResult: The result of execution (success or failure)
            
        Note:
            - This method should NEVER raise exceptions
            - All errors must be captured in StepResult.error
            - The method should be idempotent when possible
        """
        ...


# ============================================================================
# Task 0.2.0.2: StepResult Structure (Placeholder for next task)
# ============================================================================

@dataclass
class StepResult:
    """
    The standardized result shape returned by all step executors.
    
    This structure ensures:
    - Predictable output format for the executor
    - Clear success/failure semantics
    - Structured error information for debugging
    - Metadata for observability
    
    Properties:
        status: Either "success" or "failure"
        output: The step's output data (only present on success)
        error: Error information (only present on failure)
        metadata: Additional execution metadata (e.g., duration)
    """
    
    status: str  # "success" | "failure"
    output: Optional[Any] = None  # Present on success
    error: Optional["StepError"] = None  # Present on failure
    metadata: Optional["StepMetadata"] = None  # Always present
    
    def __post_init__(self):
        """Validate the result structure."""
        if self.status not in ("success", "failure"):
            raise ValueError(f"Invalid status: {self.status}. Must be 'success' or 'failure'")
        
        if self.status == "success" and self.error is not None:
            raise ValueError("Success result cannot have an error")
        
        if self.status == "failure" and self.error is None:
            raise ValueError("Failure result must have an error")


@dataclass
class StepError:
    """
    Structured error information for failed step executions.
    
    Properties:
        code: Machine-readable error code (e.g., "TIMEOUT", "VALIDATION_FAILED")
        message: Human-readable error message
        retryable: Whether this error is transient and can be retried
        error_type: Classification of error - "transient" or "permanent"
    
    Error Types:
        - transient: Temporary failures (network issues, rate limits, timeouts)
        - permanent: Permanent failures (validation errors, bad data, logic errors)
    
    Note:
        Detailed error taxonomy and retry logic come in Phase 1.
        For Phase 0, we keep this minimal but extensible.
    """
    
    code: str
    message: str
    retryable: bool = False  # Conservative default: assume not retryable
    error_type: str = "permanent"  # "transient" | "permanent"
    
    def __post_init__(self):
        """Validate error_type."""
        if self.error_type not in ("transient", "permanent"):
            raise ValueError(f"Invalid error_type: {self.error_type}. Must be 'transient' or 'permanent'")


@dataclass
class StepMetadata:
    """
    Execution metadata for observability.
    
    Properties:
        duration_ms: How long the step took to execute (in milliseconds)
        started_at: When execution started
        finished_at: When execution finished
    
    Note:
        Rich observability (traces, metrics) comes in Phase 8.
        For Phase 0, we track just the basics.
    """
    
    duration_ms: int
    started_at: datetime
    finished_at: datetime


# ============================================================================
# Task 0.2.0.3: ExecutionContext (Placeholder for next task)
# ============================================================================

@dataclass
class ExecutionContext:
    """
    Runtime context provided to every step execution.
    
    This context provides:
    - Execution identifiers (for logging and persistence)
    - Trigger input (the original workflow input)
    - Shared execution metadata
    
    Design principle: Keep context MINIMAL.
    - Steps should be stateless
    - Steps should not depend on other steps' outputs directly
    - The executor manages data flow, not the steps
    
    Properties:
        workflow_execution_id: ID of the current workflow execution
        step_execution_id: ID of the current step execution
        workflow_id: ID of the workflow definition
        step_id: ID of the step definition
        trigger_input: The original input that triggered the workflow
    """
    
    workflow_execution_id: UUID
    step_execution_id: UUID
    workflow_id: UUID
    step_id: UUID
    trigger_input: Any  # The original workflow trigger data
    
    # Future phases may add:
    # - user_id: UUID (for multi-tenancy in Phase 8)
    # - trace_id: str (for distributed tracing in Phase 8)
    # - timeout_at: datetime (for timeout handling in Phase 2)
