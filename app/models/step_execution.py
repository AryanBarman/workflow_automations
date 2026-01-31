"""
StepExecution model - represents the execution of one step within a workflow execution.

A step execution is:
- Evidence of what actually happened
- Contains input, output, errors, metadata
- Never overwritten
"""

from datetime import datetime
from uuid import uuid4
import enum

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.core.exceptions import InvalidStateTransitionError


class StepExecutionStatus(str, enum.Enum):
    """Valid step execution states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepExecution(Base):
    """
    StepExecution entity - the execution of one step within a workflow execution.
    
    Properties:
        id: Unique identifier
        workflow_execution_id: Reference to parent workflow execution
        step_id: Reference to step definition
        status: Current execution status
        input: Input data provided to step
        output: Output data produced by step
        error: Error message if failed
        started_at: When step execution began
        finished_at: When step execution completed
    """
    
    __tablename__ = "step_executions"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    # Foreign keys
    workflow_execution_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    step_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Core fields
    status: Mapped[StepExecutionStatus] = mapped_column(
        SQLEnum(StepExecutionStatus, name="step_execution_status"),
        nullable=False,
        default=StepExecutionStatus.PENDING,
        index=True
    )
    
    # Execution data (stored as JSON for flexibility)
    input: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "transient" | "permanent"
    
    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    workflow_execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution",
        back_populates="step_executions"
    )
    
    step: Mapped["Step"] = relationship(
        "Step",
        back_populates="executions"
    )
    
    logs: Mapped[list["ExecutionLog"]] = relationship(
        "ExecutionLog",
        back_populates="step_execution",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<StepExecution(id={self.id}, status={self.status})>"
    
    @property
    def is_terminal(self) -> bool:
        """Check if step execution is in a terminal state."""
        return self.status in {
            StepExecutionStatus.SUCCESS,
            StepExecutionStatus.FAILED,
            StepExecutionStatus.SKIPPED
        }
    
    def transition_to(self, new_status: StepExecutionStatus) -> None:
        """
        Transition the step execution to a new status.
        
        This method enforces the state machine rules:
        - pending → running (valid)
        - running → success|failed|skipped (valid)
        - terminal → * (invalid - terminal states are immutable)
        - Any other transition (invalid)
        
        Args:
            new_status: The target status to transition to
            
        Raises:
            InvalidStateTransitionError: If the transition is not allowed
            
        Side effects:
            - Sets started_at when transitioning to RUNNING
            - Sets finished_at when transitioning to terminal state
        """
        current_status = self.status
        
        # Enforce immutability: terminal states cannot be changed
        if self.is_terminal:
            raise InvalidStateTransitionError(
                from_state=current_status.value,
                to_state=new_status.value
            )
        
        # Validate the transition is allowed
        if not self._validate_transition(current_status, new_status):
            raise InvalidStateTransitionError(
                from_state=current_status.value,
                to_state=new_status.value
            )
        
        # Perform the transition
        self.status = new_status
        
        # Set timestamps based on the new state
        if new_status == StepExecutionStatus.RUNNING:
            self.started_at = datetime.utcnow()
        
        if new_status in {
            StepExecutionStatus.SUCCESS,
            StepExecutionStatus.FAILED,
            StepExecutionStatus.SKIPPED
        }:
            self.finished_at = datetime.utcnow()
    
    def _validate_transition(
        self,
        from_status: StepExecutionStatus,
        to_status: StepExecutionStatus
    ) -> bool:
        """
        Validate if a state transition is allowed.
        
        Valid transitions:
        - PENDING → RUNNING
        - RUNNING → SUCCESS
        - RUNNING → FAILED
        - RUNNING → SKIPPED
        
        Args:
            from_status: Current status
            to_status: Target status
            
        Returns:
            True if transition is valid, False otherwise
        """
        valid_transitions = {
            StepExecutionStatus.PENDING: {
                StepExecutionStatus.RUNNING
            },
            StepExecutionStatus.RUNNING: {
                StepExecutionStatus.SUCCESS,
                StepExecutionStatus.FAILED,
                StepExecutionStatus.SKIPPED
            }
        }
        
        allowed_targets = valid_transitions.get(from_status, set())
        return to_status in allowed_targets
