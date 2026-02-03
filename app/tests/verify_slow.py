
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.workflow import Workflow
from app.models.step import Step
from app.executor.linear_executor import LinearExecutor

def test_slow_workflow():
    # Setup database (Sync)
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        # 1. Find the latest "Workflow — Timeout Test"
        workflow = session.query(Workflow).filter(Workflow.name == "Workflow — Timeout Test").order_by(Workflow.created_at.desc()).first()
        
        if not workflow:
            print("❌ Workflow not found. Please run add_slow_workflow.py first.")
            return

        print(f"✅ Found workflow: {workflow.name} (ID: {workflow.id})")
        
        # 2. Run executor
        executor = LinearExecutor(session)
        print("🚀 Executing slow workflow (Expect Failure)...")
        execution = executor.execute(workflow, {})
        
        print(f"🏁 Execution Status: {execution.status}")
        
        if execution.status == "FAILED":
            # Check step failure code
            from app.models.step_execution import StepExecution, StepExecutionStatus
            failed_step = session.query(StepExecution).filter(
                StepExecution.workflow_execution_id == execution.id,
                StepExecution.status == StepExecutionStatus.FAILED
            ).first()
            
            if failed_step and "TIMEOUT" in failed_step.error:
                 print(f"✅ Verified: Step failed with TIMEOUT error: {failed_step.error}")
            else:
                 print(f"❌ Failed but not due to timeout? Error: {failed_step.error if failed_step else 'None'}")
        else:
            print(f"❌ Workflow should have failed but got {execution.status}")

    except Exception as e:
        print(f"💥 Error during test: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_slow_workflow()
