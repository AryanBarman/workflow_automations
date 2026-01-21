"""
Step model - represents a single unit of work within a workflow.

A step is:
- Declarative, not executable
- Has a strict type (manual | ai | api | logic)
- Contains configuration as JSON
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.core.database import Base


class StepType(str, enum.Enum):
    """Valid step types."""
    MANUAL = "manual"
    AI = "ai"
    API = "api"
    LOGIC = "logic"


class Step(Base):
    """
    Step entity - a single unit of work inside a workflow.
    
    Properties:
        id: Unique identifier
        workflow_id: Reference to parent workflow
        type: Type of step (manual | ai | api | logic)
        config: JSON configuration (opaque to UI)
        order: Execution order within workflow
        created_at: Timestamp of creation
    """
    
    __tablename__ = "steps"
    
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
    type: Mapped[StepType] = mapped_column(
        SQLEnum(StepType, name="step_type"),
        nullable=False
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="steps"
    )
    
    executions: Mapped[list["StepExecution"]] = relationship(
        "StepExecution",
        back_populates="step"
    )
    
    def __repr__(self) -> str:
        return f"<Step(id={self.id}, type={self.type}, order={self.order})>"
