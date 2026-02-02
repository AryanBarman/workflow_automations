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


@router.post("/{execution_id}/steps/{step_execution_id}/retry", response_model=WorkflowExecutionSchema)
async def retry_step(execution_id: UUID, step_execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Manually retry a failed step.
    
    This creates a new StepExecution record (append-only) and triggers
    synchronous execution of the step, then potentially resumes the workflow.
    
    Args:
        execution_id: UUID of the workflow execution
        step_execution_id: UUID of the FAILED StepExecution to retry
        
    Returns:
        Updated workflow execution status
        
    Raises:
        HTTPException: 404 if not found, 400 if not retryable
    """
    # Check execution existence
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # IMPORTANT: Phase 1 simplification
    # We are calling the Synchronous LinearExecutor from an Async Route.
    # We must use a synchronous session for the executor.
    # In a real app, this would offload to a Celery worker.
    # Here, we bridge the gap by creating a sync session on the fly OR 
    # (better for now) just using the async logic if LinearExecutor was async.
    #
    # Since LinearExecutor is SYNC and uses blocking IO (Task 0.3.3 spec),
    # we have to run it in a threadpool or similar.
    # BUT, to keep it "boring and simple" for Phase 1Prototype:
    # We will instantiate a sync session just for this operation.
    
    from app.core.database import SessionLocal  # Sync session factory
    from app.executor.linear_executor import LinearExecutor
    
    try:
        # Run synchronous executor logic
        with SessionLocal() as sync_db:
            executor = LinearExecutor(sync_db)
            
            # Check if step execution exists and is failed (validation)
            # define valid state
            
            try:
                updated_execution = executor.resume_execution(str(execution_id), str(step_execution_id))
            except ValueError as e:
                 raise HTTPException(status_code=400, detail=str(e))
                 
            # Re-fetch with async session to return Pydantic model
            # (Or just return the sync object converted)
            
    except Exception as e:
        # Catch-all for executor errors
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")
        
    # Re-fetch updated state to return to UI
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.id == execution_id)
        .options(selectinload(WorkflowExecution.step_executions))
    )
    updated_execution = result.scalar_one_or_none()
    
    return updated_execution
