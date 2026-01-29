"""
Pydantic schemas for API responses - Task 1.1.1 & 1.1.2

These schemas define the JSON structure for API responses.
They serialize SQLAlchemy models into JSON-safe dictionaries.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class WorkflowSchema(BaseModel):
    """Schema for Workflow API response (list view)."""
    
    id: UUID
    name: str
    version: int
    description: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StepSchema(BaseModel):
    """Schema for Step API response."""
    
    id: UUID
    workflow_id: UUID
    type: str
    order: int
    config: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowDetailSchema(BaseModel):
    """Schema for Workflow detail API response (includes steps)."""
    
    id: UUID
    name: str
    version: int
    description: Optional[str] = None
    created_at: datetime
    steps: List[StepSchema] = []
    
    model_config = ConfigDict(from_attributes=True)
