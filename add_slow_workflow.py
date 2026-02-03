
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.models.workflow import Workflow
from app.models.step import Step, StepType
from app.config import settings

# Setup sync database connection
DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def seed_slow_workflow():
    session = SessionLocal()
    try:
        # Create "Slow Workflow"
        workflow = Workflow(
            name="Workflow — Timeout Test",
            version=1,
            created_by="test_user"
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)
        
        # Step 1: Sleep 5s, Timeout 2s
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.LOGIC,
            config={
                "description": "Sleep for 5 seconds",
                "sleep": 5
            },
            timeout_seconds=2, # Should fail
            order=1
        )
        session.add(step1)
        
        session.commit()
        print(f"✅ Created 'Workflow — Timeout Test' (ID: {workflow.id})")
        
    except Exception as e:
        print(f"❌ Error seeding workflow: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_slow_workflow()
