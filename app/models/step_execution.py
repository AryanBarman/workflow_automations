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

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


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
    input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
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
