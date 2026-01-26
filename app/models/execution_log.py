"""
ExecutionLog Model - Phase 0, Slice 0.5, Task 0.5.1

Stores log entries for workflow and step execution events.
Enables inspection of what happened during execution.

Each log entry captures:
- Timestamp: When the event occurred
- Message: What happened
- Metadata: Additional context (JSON)
- Link to StepExecution: Which step this log belongs to (nullable for workflow-level logs)
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ExecutionLog(Base):
    """
    ExecutionLog - Stores log entries for execution events.
    
    This model captures events that occur during workflow and step execution,
    providing an audit trail and debugging information.
    
    For Phase 0, logs are simple timestamped messages with optional metadata.
    Future phases may add log levels, severity, or structured logging.
    """
    
    __tablename__ = "execution_logs"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # Foreign key to StepExecution (nullable for workflow-level logs)
    step_execution_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("step_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Log data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Relationship to StepExecution
    step_execution: Mapped["StepExecution"] = relationship(
        "StepExecution",
        back_populates="logs"
    )
    
    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, step_execution_id={self.step_execution_id}, message={self.message[:50]}...)>"
