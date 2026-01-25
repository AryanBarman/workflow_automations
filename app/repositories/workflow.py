"""
Workflow repository for workflow and step entities.

Provides specialized operations for workflow management.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Workflow, Step
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for Workflow entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Workflow, session)
    
    async def get_by_id_with_steps(self, id: UUID) -> Optional[Workflow]:
        """
        Get workflow by ID with all steps eagerly loaded.
        
        Args:
            id: Workflow UUID
            
        Returns:
            Workflow with steps if found, None otherwise
        """
        result = await self.session.execute(
            select(Workflow)
            .options(selectinload(Workflow.steps))
            .where(Workflow.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name_and_version(
        self, name: str, version: int
    ) -> Optional[Workflow]:
        """
        Get workflow by name and version.
        
        Args:
            name: Workflow name
            version: Workflow version
            
        Returns:
            Workflow if found, None otherwise
        """
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.name == name, Workflow.version == version)
        )
        return result.scalar_one_or_none()
    
    async def create_with_steps(
        self,
        name: str,
        created_by: str,
        steps_data: List[dict],
        version: int = 1
    ) -> Workflow:
        """
        Create workflow with steps in a single transaction.
        
        Args:
            name: Workflow name
            created_by: User creating the workflow
            steps_data: List of step configurations
            version: Workflow version
            
        Returns:
            Created workflow with steps
        """
        # Create workflow
        workflow = Workflow(
            name=name,
            version=version,
            created_by=created_by
        )
        self.session.add(workflow)
        
        # Create steps
        for step_data in steps_data:
            step = Step(
                workflow=workflow,
                type=step_data["type"],
                config=step_data.get("config", {}),
                order=step_data["order"]
            )
            self.session.add(step)
        
        await self.session.commit()
        await self.session.refresh(workflow)
        
        # Load steps
        result = await self.session.execute(
            select(Workflow)
            .options(selectinload(Workflow.steps))
            .where(Workflow.id == workflow.id)
        )
        return result.scalar_one()


class StepRepository(BaseRepository[Step]):
    """Repository for Step entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Step, session)
    
    async def get_by_workflow_id(self, workflow_id: UUID) -> List[Step]:
        """
        Get all steps for a workflow, ordered by execution order.
        
        Args:
            workflow_id: Workflow UUID
            
        Returns:
            List of steps ordered by execution order
        """
        result = await self.session.execute(
            select(Step)
            .where(Step.workflow_id == workflow_id)
            .order_by(Step.order)
        )
        return list(result.scalars().all())
