"""
Workflow API routes - Task 1.1.1

REST API endpoints for workflow operations.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import Workflow
from app.schemas import WorkflowSchema

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
