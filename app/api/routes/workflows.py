"""
Workflow API routes - Task 1.1.1, 1.1.2 & 1.1.3

REST API endpoints for workflow operations.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Workflow
from app.schemas import WorkflowSchema, WorkflowDetailSchema, ExecuteWorkflowRequest, ExecuteWorkflowResponse
from app.executor import LinearExecutor

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("", response_model=List[WorkflowSchema])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    """
    Get all workflows.
    
    Returns:
        List of all workflow definitions in the database.
    """
    result = await db.execute(select(Workflow))
    workflows = result.scalars().all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowDetailSchema)
async def get_workflow(workflow_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get a single workflow by ID, including its steps.
    
    Args:
        workflow_id: UUID of the workflow to retrieve
        
    Returns:
        Workflow with nested steps, ordered by step order
        
    Raises:
        HTTPException: 404 if workflow not found
    """
    # Query with eager loading of steps relationship
    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one_or_none()
    
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return workflow


@router.post("/{workflow_id}/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(
    workflow_id: UUID,
    request: ExecuteWorkflowRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a workflow.
    
    Triggers synchronous execution of the specified workflow.
    Returns after execution completes with execution ID and final status.
    
    Note: Execution is currently synchronous. Async execution will be added in later phase.
    
    Args:
        workflow_id: UUID of the workflow to execute
        request: Execution request with optional trigger input
        
    Returns:
        Execution ID and final status
        
    Raises:
        HTTPException: 404 if workflow not found
    """
    # Check workflow exists
    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one_or_none()
    
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    # Execute workflow synchronously using run_sync
    def _execute_sync(sync_session):
        executor = LinearExecutor(sync_session)
        return executor.execute(workflow, request.trigger_input or {})
    
    execution = await db.run_sync(_execute_sync)
    
    # Commit to persist execution
    await db.commit()
    await db.refresh(execution)
    
    return ExecuteWorkflowResponse(
        execution_id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        started_at=execution.started_at
    )
