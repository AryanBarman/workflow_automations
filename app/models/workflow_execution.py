"""
WorkflowExecution model - represents a single attempt to execute a workflow.

A workflow execution is:
- Immutable history
- Has a lifecycle (pending → running → terminal)
- Never overwritten
"""

from datetime import datetime
from uuid import uuid4
import enum

from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class WorkflowExecutionStatus(str, enum.Enum):
    """Valid workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowExecution(Base):
    """
    WorkflowExecution entity - a single attempt to run a workflow.
    
    Properties:
        id: Unique identifier
        workflow_id: Reference to workflow definition
        workflow_version: Version of workflow being executed
        status: Current execution status
        trigger_source: How this execution was triggered
        started_at: When execution began
        finished_at: When execution completed (if terminal)
    """
    
    __tablename__ = "workflow_executions"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    # Foreign key
    workflow_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Core fields
    workflow_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkflowExecutionStatus] = mapped_column(
        SQLEnum(WorkflowExecutionStatus, name="workflow_execution_status"),
        nullable=False,
        default=WorkflowExecutionStatus.PENDING,
        index=True
    )
    trigger_source: Mapped[str] = mapped_column(String(255), nullable=False)
    
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
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="executions"
    )
    
    step_executions: Mapped[list["StepExecution"]] = relationship(
        "StepExecution",
        back_populates="workflow_execution",
        cascade="all, delete-orphan",
        order_by="StepExecution.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, status={self.status})>"
    
    @property
    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.status in {
            WorkflowExecutionStatus.SUCCESS,
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.CANCELLED
        }
