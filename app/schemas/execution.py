"""
Pydantic schemas for execution API requests/responses - Task 1.1.3, 1.1.4 & 1.1.5

These schemas define the JSON structure for execution-related API operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ExecuteWorkflowRequest(BaseModel):
    """Schema for workflow execution request."""
    
    trigger_input: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExecuteWorkflowResponse(BaseModel):
    """Schema for workflow execution response."""
    
    execution_id: UUID
    workflow_id: UUID
    status: str
    started_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StepExecutionSchema(BaseModel):
    """Schema for step execution details."""
    
    id: UUID
    step_id: UUID
    status: str
    input: Optional[dict] = None
    output: Optional[dict] = None
    error: Optional[str] = None
    error_type: Optional[str] = None  # "transient" | "permanent"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionSchema(BaseModel):
    """Schema for workflow execution details."""
    
    id: UUID
    workflow_id: UUID
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    step_executions: Optional[List[StepExecutionSchema]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionLogSchema(BaseModel):
    """Schema for execution log entries."""
    
    id: UUID
    workflow_execution_id: UUID
    step_execution_id: Optional[UUID] = None
    event_type: str
    message: str
    timestamp: datetime
    metadata: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)
