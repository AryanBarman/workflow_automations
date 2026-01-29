"""
Execution API routes - Task 1.1.4 & 1.1.5

REST API endpoints for execution operations.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import WorkflowExecution, ExecutionLog
from app.schemas.execution import WorkflowExecutionSchema, ExecutionLogSchema

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("/{execution_id}", response_model=WorkflowExecutionSchema)
async def get_execution(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get execution status by ID.
    
    Returns the current state of a workflow execution including status,
    timestamps, and step execution details.
    
    Args:
        execution_id: UUID of the execution to retrieve
        
    Returns:
        Execution details with status and step executions
        
    Raises:
        HTTPException: 404 if execution not found
    """
    # Query with eager loading of step_executions relationship
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.id == execution_id)
        .options(selectinload(WorkflowExecution.step_executions))
    )
    execution = result.scalar_one_or_none()
    
    if execution is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return execution


@router.get("/{execution_id}/logs", response_model=List[ExecutionLogSchema])
async def get_execution_logs(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get execution logs by execution ID.
    
    Returns all logs for a workflow execution in chronological order.
    Includes workflow-level and step-level lifecycle events.
    
    Args:
        execution_id: UUID of the execution
        
    Returns:
        List of execution logs ordered by timestamp
        
    Raises:
        HTTPException: 404 if execution not found
    """
    # Check execution exists
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if execution is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Get logs ordered by timestamp
    logs_result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.workflow_execution_id == execution_id)
        .order_by(ExecutionLog.timestamp)
    )
    logs = logs_result.scalars().all()
    
    return logs
