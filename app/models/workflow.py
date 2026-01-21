"""
Workflow model - represents a reusable workflow definition.

A workflow is:
- Static and versioned
- A reusable definition of intent
- Does not know when it will run
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Workflow(Base):
    """
    Workflow entity - a reusable, versioned definition of ordered steps.
    
    Properties:
        id: Unique identifier
        name: Human-readable workflow name
        version: Version number for tracking changes
        created_by: User who created this workflow
        created_at: Timestamp of creation
        steps: List of Step entities belonging to this workflow
    """
    
    __tablename__ = "workflows"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    steps: Mapped[List["Step"]] = relationship(
        "Step",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="Step.order"
    )
    
    executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow"
    )
    
    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name='{self.name}', version={self.version})>"
