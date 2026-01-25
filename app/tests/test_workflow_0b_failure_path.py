"""
Workflow 0B — Failure Path

This test validates the failure path execution flow where a step fails.

Workflow Definition:
- Step 1: InputStep (MANUAL) - Accepts input data (succeeds)
- Step 2: FailStep (API) - Always fails
- Step 3: PersistStep (STORAGE) - Should NOT execute (execution stops at step 2)

Expected Result:
- Step 1 executes successfully
- Step 2 fails
- Step 3 does NOT execute
- WorkflowExecution status: FAILED

Note: Fixtures (db_session, workflow_0b_failure_path) are defined in conftest.py
"""

from app.models.workflow_execution import WorkflowExecutionStatus
from app.models.step_execution import StepExecution, StepExecutionStatus
from app.executor import LinearExecutor


class TestWorkflow0BFailurePath:
    """Test Workflow 0B — Failure Path execution."""
    
    def test_workflow_fails(self, db_session, workflow_0b_failure_path):
        """Test that Workflow 0B fails."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Workflow should complete with FAILED
        assert execution.status == WorkflowExecutionStatus.FAILED
    
    def test_only_two_steps_execute(self, db_session, workflow_0b_failure_path):
        """Test that only first two steps execute (execution stops at failure)."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Should have only 2 step executions (step 3 not executed)
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        assert len(step_executions) == 2
    
    def test_first_step_succeeds_second_fails(self, db_session, workflow_0b_failure_path):
        """Test that first step succeeds and second step fails."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # First step should be SUCCESS
        assert step_executions[0].status == StepExecutionStatus.SUCCESS
        
        # Second step should be FAILED
        assert step_executions[1].status == StepExecutionStatus.FAILED
    
    def test_failed_step_has_error(self, db_session, workflow_0b_failure_path):
        """Test that failed step has error message."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # Second step should have error
        assert step_executions[1].error is not None
        assert "FORCED_FAILURE" in step_executions[1].error
    
    def test_workflow_is_terminal(self, db_session, workflow_0b_failure_path):
        """Test that workflow is in terminal state after failure."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        assert execution.is_terminal
    
    def test_workflow_has_finished_timestamp(self, db_session, workflow_0b_failure_path):
        """Test that workflow has finished_at timestamp even on failure."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        assert execution.finished_at is not None
    
    def test_data_flows_to_failed_step(self, db_session, workflow_0b_failure_path):
        """Test that data flows correctly to the failed step."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # Step 1 (InputStep): input should equal trigger_input
        assert step_executions[0].input == trigger_input
        
        # Step 2 (FailStep): input should be step1's output
        assert step_executions[1].input == step_executions[0].output
