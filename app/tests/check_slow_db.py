
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.models.step_execution import StepExecution, StepExecutionStatus

def check_slow_db():
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Get latest execution for Timeout Test workflow
        workflow = session.query(Workflow).filter(Workflow.name == "Workflow — Timeout Test").order_by(Workflow.created_at.desc()).first()
        if not workflow:
            print("No workflow found.")
            return

        execution = session.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow.id
        ).order_by(WorkflowExecution.created_at.desc()).first()
        
        if not execution:
            print("No execution found.")
            return
            
        print(f"Latest Execution Status: {execution.status}")
        
        # Check steps in the Workflow Definition
        from app.models.step import Step
        def_steps = session.query(Step).filter(Step.workflow_id == workflow.id).all()
        print(f"Workflow Definition has {len(def_steps)} steps.")
        for s in def_steps:
             print(f"  Def Step: {s.id} Order: {s.order} Config: {s.config}")
        
        # Check Execution Steps
        steps = session.query(StepExecution).filter(
            StepExecution.workflow_execution_id == execution.id
        ).all()
        print(f"Workflow Execution has {len(steps)} step executions.")
        
        for step in steps:
            print(f"Step ID: {step.step_id} Status: {step.status}")
            if step.error:
                print(f"  Error: {step.error}")

    finally:
        session.close()

if __name__ == "__main__":
    check_slow_db()
