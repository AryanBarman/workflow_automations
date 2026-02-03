
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

def seed_workflow():
    session = SessionLocal()
    try:
        # Create "Weather Logger" workflow
        workflow = Workflow(
            name="Workflow — Weather Log",
            version=1,
            created_by="demo_user"
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)
        
        # Step 1: Fetch Weather (HTTP)
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.API,
            config={
                "description": "Fetch weather for Paris",
                "handler": "http",
                "url": "https://wttr.in/Paris?format=j1",
                "method": "GET",
                "timeout": 10,
                "headers_from_input": True
            },
            order=1
        )
        session.add(step1)
        
        # Step 2: Format Weather (Logic)
        step2 = Step(
            workflow_id=workflow.id,
            type=StepType.LOGIC,
            config={
                "description": "Format weather data",
                "handler": "weather_formatter"
            },
            order=2
        )
        session.add(step2)
        
        # Step 3: Save to File (Storage)
        # Use absolute path for reliability in demo
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(current_dir, "weather_log.txt")
        
        step3 = Step(
            workflow_id=workflow.id,
            type=StepType.STORAGE,
            config={
                "description": "Append to log file",
                "path": log_path,
                "handler": "file_append"
            },
            order=3
        )
        session.add(step3)
        
        session.commit()
        print(f"✅ Created 'Workflow — Weather Log'")
        print(f"   Log file will be at: {log_path}")
        
    except Exception as e:
        print(f"❌ Error seeding workflow: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_workflow()
