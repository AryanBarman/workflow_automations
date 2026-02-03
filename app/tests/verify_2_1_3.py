
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.workflow import Workflow
from app.models.step_execution import StepExecution

def verify_headers_used():
    # Setup database (Sync)
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        # Find latest StepExecution for the FIRST step (API)
        from app.models.step import Step
        from app.models.step_execution import StepExecution
        
        latest_first_step_exec = session.query(StepExecution).join(Step).filter(
            Step.order == 1
        ).order_by(StepExecution.created_at.desc()).first()
        
        if latest_first_step_exec:
            print(f"✅ Found latest first-step execution ID: {latest_first_step_exec.workflow_execution_id}")
            print(f"Input used: {latest_first_step_exec.input}")
            if "_headers" in latest_first_step_exec.input:
                print("✅ Dynamic headers were present in input.")
            else:
                print("❌ Dynamic headers missing from input.")
        else:
            print("❌ No execution found for first step.")

    finally:
        session.close()

if __name__ == "__main__":
    verify_headers_used()
