"""
Execution repository for workflow execution and step execution entities.

Provides specialized operations for execution tracking and history.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowExecution, StepExecution, WorkflowExecutionStatus
from app.repositories.base import BaseRepository
from app.core.exceptions import ImmutabilityViolationError


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    """Repository for WorkflowExecution entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(WorkflowExecution, session)
    
    async def get_by_id_with_steps(self, id: UUID) -> Optional[WorkflowExecution]:
        """
        Get workflow execution by ID with all step executions eagerly loaded.
        
        Args:
            id: WorkflowExecution UUID
            
        Returns:
            WorkflowExecution with step executions if found, None otherwise
        """
        result = await self.session.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.step_executions))
            .where(WorkflowExecution.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_workflow_id(
        self, workflow_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[WorkflowExecution]:
        """
        Get all executions for a workflow.
        
        Args:
            workflow_id: Workflow UUID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of workflow executions
        """
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_status(
        self, id: UUID, status: WorkflowExecutionStatus
    ) -> Optional[WorkflowExecution]:
        """
        Update execution status.
        
        Note: This is one of the few allowed mutations.
        Status transitions are validated by the service layer.
        
        Args:
            id: WorkflowExecution UUID
            status: New status
            
        Returns:
            Updated execution if found, None otherwise
            
        Raises:
            ImmutabilityViolationError: If execution is in terminal state
        """
        execution = await self.get_by_id(id)
        if not execution:
            return None
        
        # Enforce immutability for terminal states
        if execution.is_terminal:
            raise ImmutabilityViolationError("WorkflowExecution", str(id))
        
        execution.status = status
        await self.session.commit()
        await self.session.refresh(execution)
        return execution


class StepExecutionRepository(BaseRepository[StepExecution]):
    """Repository for StepExecution entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(StepExecution, session)
    
    async def get_by_workflow_execution_id(
        self, workflow_execution_id: UUID
    ) -> List[StepExecution]:
        """
        Get all step executions for a workflow execution.
        
        Args:
            workflow_execution_id: WorkflowExecution UUID
            
        Returns:
            List of step executions ordered by creation time
        """
        result = await self.session.execute(
            select(StepExecution)
            .where(StepExecution.workflow_execution_id == workflow_execution_id)
            .order_by(StepExecution.created_at)
        )
        return list(result.scalars().all())
    
    async def update_status(
        self, id: UUID, status, output: Optional[dict] = None, error: Optional[str] = None
    ) -> Optional[StepExecution]:
        """
        Update step execution status and optionally output/error.
        
        Note: This is one of the few allowed mutations.
        Once terminal, no further updates are allowed.
        
        Args:
            id: StepExecution UUID
            status: New status
            output: Optional output data
            error: Optional error message
            
        Returns:
            Updated step execution if found, None otherwise
            
        Raises:
            ImmutabilityViolationError: If execution is in terminal state
        """
        step_execution = await self.get_by_id(id)
        if not step_execution:
            return None
        
        # Enforce immutability for terminal states
        if step_execution.is_terminal:
            raise ImmutabilityViolationError("StepExecution", str(id))
        
        step_execution.status = status
        if output is not None:
            step_execution.output = output
        if error is not None:
            step_execution.error = error
        
        await self.session.commit()
        await self.session.refresh(step_execution)
        return step_execution
