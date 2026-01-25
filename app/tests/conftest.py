"""
Pytest configuration and fixtures.
"""

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base


# Test database URL (use in-memory or separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/workflow_automation_test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    Each test gets a fresh database with all tables created.
    """
    # Create test engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


# ============================================================================
# Synchronous SQLite fixtures for unit tests
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.workflow import Workflow
from app.models.step import Step, StepType
from app.models.workflow_execution import WorkflowExecution
from app.models.step_execution import StepExecution


@pytest.fixture
def db_session():
    """
    Create an in-memory SQLite database for testing.
    
    This fixture is shared across all unit tests to avoid duplication.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create tables
    Workflow.__table__.create(engine, checkfirst=True)
    Step.__table__.create(engine, checkfirst=True)
    WorkflowExecution.__table__.create(engine, checkfirst=True)
    StepExecution.__table__.create(engine, checkfirst=True)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def workflow_0a_happy_path(db_session):
    """
    Create Workflow 0A — Happy Path.
    
    Steps: InputStep → TransformStep → PersistStep
    Expected: All steps succeed, workflow succeeds
    
    This is the canonical happy path workflow for Phase 0.
    """
    # Create workflow
    workflow = Workflow(
        name="Workflow 0A — Happy Path",
        version=1,
        created_by="test_system"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    
    # Create steps
    step1 = Step(
        workflow_id=workflow.id,
        type=StepType.MANUAL,  # InputStep
        config={"description": "Accept user input"},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.LOGIC,  # TransformStep
        config={"description": "Transform data"},
        order=2
    )
    step3 = Step(
        workflow_id=workflow.id,
        type=StepType.STORAGE,  # PersistStep
        config={"description": "Persist data"},
        order=3
    )
    
    db_session.add_all([step1, step2, step3])
    db_session.commit()
    
    return workflow


@pytest.fixture
def workflow_0b_failure_path(db_session):
    """
    Create Workflow 0B — Failure Path.
    
    Steps: InputStep → FailStep → PersistStep (not executed)
    Expected: Step 2 fails, workflow fails, step 3 doesn't execute
    
    This is the canonical failure path workflow for Phase 0.
    """
    # Create workflow
    workflow = Workflow(
        name="Workflow 0B — Failure Path",
        version=1,
        created_by="test_system"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    
    # Create steps
    step1 = Step(
        workflow_id=workflow.id,
        type=StepType.MANUAL,  # InputStep - succeeds
        config={"description": "Accept user input"},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.API,  # FailStep - always fails
        config={"description": "API call that fails"},
        order=2
    )
    step3 = Step(
        workflow_id=workflow.id,
        type=StepType.STORAGE,  # PersistStep - should not execute
        config={"description": "Persist data (not executed)"},
        order=3
    )
    
    db_session.add_all([step1, step2, step3])
    db_session.commit()
    
    return workflow

