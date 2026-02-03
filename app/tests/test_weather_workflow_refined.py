
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
import uuid

def test_refined_weather_workflow():
    # Setup database (Sync)
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        # 1. Find the latest "Workflow — Weather Log"
        workflow = session.query(Workflow).filter(Workflow.name == "Workflow — Weather Log").order_by(Workflow.id.desc()).first()
        
        if not workflow:
            print("❌ Workflow not found. Please run add_weather_workflow.py first.")
            return

        print(f"✅ Found workflow: {workflow.name} (ID: {workflow.id})")
        
        # 2. Create initial input with dynamic headers
        initial_input = {
            "_headers": {
                "User-Agent": "Refined-Weather-Bot/2.0",
                "X-Refinement-Test": "True"
            }
        }
        
        # 3. Run executor (Sync)
        executor = LinearExecutor(session)
        print("🚀 Executing refined weather workflow...")
        execution = executor.execute(workflow, initial_input)
        
        print(f"🏁 Execution Status: {execution.status}")
        
        if execution.status == "SUCCESS":
            print("✅ Workflow executed successfully!")
            
            # Find the output of the last step (Step 3: storage)
            # Or just check the log file
            steps = session.query(Step).filter(Step.workflow_id == workflow.id).order_by(Step.order).all()
            log_path = steps[2].config.get("path")
            
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        print(f"📄 Last log entry: {last_line.strip()}")
                    else:
                        print("⚠️ Log file is empty.")
            else:
                print(f"⚠️ Log file not found at {log_path}")
        else:
            # Find the failed step execution
            from app.models.step_execution import StepExecution, StepExecutionStatus
            failed_step = session.query(StepExecution).filter(
                StepExecution.workflow_execution_id == execution.id,
                StepExecution.status == StepExecutionStatus.FAILED
            ).first()
            if failed_step:
                print(f"❌ Step failed: {failed_step.error}")
            else:
                print("❌ Workflow failed without a specific step failure captured (check logs).")

    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_refined_weather_workflow()
