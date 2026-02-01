"""
Verify Retry Logic Script

This script executes Workflow 0B and asserts:
1. Workflow finishes with SUCCESS status.
2. Step 2 (TransientFailStep) fails 2 times and succeeds on the 3rd.
3. Retry metadata is correctly logged.
"""

import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Workflow, StepExecution, StepExecutionStatus, ExecutionLog
from app.executor.linear_executor import LinearExecutor
from app.config import settings

# Create sync engine
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

def verify_retry():
    session = SessionLocal()
    try:
        # Get Workflow 0b
        workflow = session.query(Workflow).filter_by(name="Workflow 0b — Retry Test").first()
        if not workflow:
            print("❌ Workflow 0b not found! Run add_workflow_0b.py first.")
            return

        print(f"🔄 Executing Workflow 0b: {workflow.name}")
        
        # Execute workflow
        executor = LinearExecutor(session)
        execution = executor.execute(workflow, {"test": "data"})
        
        print(f"✅ Execution finished. Status: {execution.status}")
        
        # 1. Assert Workflow Status
        # Check against enum value or string
        status_value = execution.status.value if hasattr(execution.status, 'value') else str(execution.status)
        if status_value.lower() != "success":
            print(f"❌ Expected success, got {status_value}")
            print_debug_info(execution.id, session)
            sys.exit(1)
            
        # 2. Assert Step 2 Executions
        # Step 2 is API type (TransientFailStep)
        # It should have 3 executions: 2 Failures, 1 Success
        step_2_executions = []
        
        # Get all step executions
        workflow_executions = session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.started_at).all()
        
        for se in workflow_executions:
            if se.step.order == 2:
                step_2_executions.append(se)
        
        print(f"\n🔍 Verifying Step 2 retry behavior:")
        if len(step_2_executions) != 3:
            print(f"❌ Expected 3 executions for Step 2, got {len(step_2_executions)}")
            print_debug_info(execution.id, session)
            sys.exit(1)
        else:
            print(f"✅ Correct number of executions for Step 2 (3)")
            
            # Check statuses
            statuses = [se.status for se in step_2_executions]
            print(f"   Statuses: {[s.value for s in statuses]}")
            
            if statuses != [StepExecutionStatus.FAILED, StepExecutionStatus.FAILED, StepExecutionStatus.SUCCESS]:
                print("❌ Unexpected status sequence. Expected [FAILED, FAILED, SUCCESS]")
                print_debug_info(execution.id, session)
                sys.exit(1)
            else:
                print("✅ Status sequence correct")
                
            # Check retry counts and parent links
            print("   Checking retry metadata...")
            initial = step_2_executions[0]
            first_retry = step_2_executions[1]
            second_retry = step_2_executions[2]
            
            if initial.retry_count != 0 or initial.is_retry:
                print(f"❌ Initial attempt metadata incorrect: retry_count={initial.retry_count}, is_retry={initial.is_retry}")
                sys.exit(1)
                
            if first_retry.retry_count != 1 or not first_retry.is_retry or first_retry.parent_step_execution_id != initial.id:
                print(f"❌ First retry metadata incorrect")
                sys.exit(1)
                
            if second_retry.retry_count != 2 or not second_retry.is_retry or second_retry.parent_step_execution_id != first_retry.id:
                print(f"❌ Second retry metadata incorrect")
                sys.exit(1)
                
            print("✅ Retry metadata correct")

        print("\n🎉 VALIDATION PASSED!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

def print_debug_info(execution_id, session):
    print("\n🐛 DEBUG SUMMARY:")
    try:
        runs = session.query(StepExecution).filter_by(workflow_execution_id=execution_id).order_by(StepExecution.started_at).all()
        for run in runs:
            print(f"Step {run.step.order} ({run.step.type.value}) - status={run.status.value}, retry={run.retry_count}, error={run.error_type}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_retry()
