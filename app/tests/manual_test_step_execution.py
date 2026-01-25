"""
Manual Integration Test for Sequential Step Execution - Task 0.3.4

This script tests the LinearExecutor with real PostgreSQL database.
Run this after the database is set up and migrations are applied.

Usage:
    python -m app.tests.manual_test_step_execution
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.database import Base
from app.models import Workflow, Step, StepType, WorkflowExecution, StepExecution
from app.executor import LinearExecutor


async def test_step_execution_async():
    """Test step execution with async PostgreSQL database."""
    # Use test database
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/workflow_automation_test_db"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create workflow
        workflow = Workflow(
            name="Test Sequential Execution",
            version=1,
            created_by="manual_test"
        )
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        
        # Create steps: Input → Transform
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.MANUAL,
            config={},
            order=1
        )
        step2 = Step(
            workflow_id=workflow.id,
            type=StepType.LOGIC,
            config={},
            order=2
        )
        
        session.add_all([step1, step2])
        await session.commit()
        
        print(f"✓ Created workflow: {workflow.id}")
        print(f"✓ Created {len([step1, step2])} steps")
        
        # Note: LinearExecutor uses synchronous session
        # For this test, we'll need to use sync session
        print("\n⚠️  LinearExecutor requires synchronous session")
        print("   This test demonstrates the workflow/step creation")
        print("   Actual execution requires sync session setup")
    
    await engine.dispose()


def test_step_execution_sync():
    """Test step execution with synchronous PostgreSQL database."""
    # Use sync database URL
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/workflow_automation_test_db"
    
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Create workflow
        workflow = Workflow(
            name="Test Sequential Execution (Sync)",
            version=1,
            created_by="manual_test"
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)
        
        # Create steps: Input → Transform
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.MANUAL,
            config={},
            order=1
        )
        step2 = Step(
            workflow_id=workflow.id,
            type=StepType.LOGIC,
            config={},
            order=2
        )
        
        session.add_all([step1, step2])
        session.commit()
        
        print(f"\n✓ Created workflow: {workflow.id}")
        print(f"✓ Created 2 steps")
        
        # Execute workflow
        print("\n🚀 Executing workflow...")
        executor = LinearExecutor(session)
        trigger_input = {"test": "data", "user_id": "123"}
        
        execution = executor.execute(workflow, trigger_input)
        
        print(f"\n✓ Workflow execution created: {execution.id}")
        print(f"✓ Status: {execution.status}")
        
        # Query step executions
        step_executions = session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        print(f"\n✓ Created {len(step_executions)} step executions:")
        for i, step_exec in enumerate(step_executions, 1):
            print(f"  {i}. Status: {step_exec.status}")
            print(f"     Input: {step_exec.input}")
            print(f"     Output: {step_exec.output}")
            if step_exec.error:
                print(f"     Error: {step_exec.error}")
        
        print("\n✅ Test completed successfully!")
        
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Manual Integration Test - Sequential Step Execution")
    print("=" * 60)
    
    print("\nRunning synchronous test...")
    test_step_execution_sync()
