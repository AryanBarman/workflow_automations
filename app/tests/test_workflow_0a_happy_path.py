"""
Workflow 0A — Happy Path

This test validates the happy path execution flow where all steps succeed.

Workflow Definition:
- Step 1: InputStep (MANUAL) - Accepts input data
- Step 2: TransformStep (LOGIC) - Transforms the data
- Step 3: PersistStep (STORAGE) - Simulates data persistence

Expected Result:
- All steps execute successfully
- WorkflowExecution status: SUCCESS
- All StepExecution statuses: SUCCESS
- Data flows correctly between steps

Note: Fixtures (db_session, workflow_0a_happy_path) are defined in conftest.py
"""

from app.models.workflow_execution import WorkflowExecutionStatus
from app.models.step_execution import StepExecution, StepExecutionStatus
from app.executor import LinearExecutor


class TestWorkflow0AHappyPath:
    """Test Workflow 0A — Happy Path execution."""
    
    def test_workflow_executes_successfully(self, db_session, workflow_0a_happy_path):
        """Test that Workflow 0A executes successfully."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Workflow should complete with SUCCESS
        assert execution.status == WorkflowExecutionStatus.SUCCESS
    
    def test_all_steps_execute(self, db_session, workflow_0a_happy_path):
        """Test that all three steps execute."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Should have 3 step executions
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        assert len(step_executions) == 3
    
    def test_all_steps_succeed(self, db_session, workflow_0a_happy_path):
        """Test that all steps have SUCCESS status."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # All steps should be SUCCESS
        for step_exec in step_executions:
            assert step_exec.status == StepExecutionStatus.SUCCESS
    
    def test_data_flows_through_steps(self, db_session, workflow_0a_happy_path):
        """Test that data flows correctly through all steps."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # Step 1 (InputStep): input should equal trigger_input, output should equal input
        assert step_executions[0].input == trigger_input
        assert step_executions[0].output == trigger_input
        
        # Step 2 (TransformStep): input should be step1's output, output should have "processed" field
        assert step_executions[1].input == step_executions[0].output
        assert "processed" in step_executions[1].output
        
        # Step 3 (PersistStep): input should be step2's output
        assert step_executions[2].input == step_executions[1].output
    
    def test_workflow_has_lifecycle_timestamps(self, db_session, workflow_0a_happy_path):
        """Test that workflow execution has complete lifecycle timestamps."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # All timestamps should be set
        assert execution.created_at is not None
        assert execution.started_at is not None
        assert execution.finished_at is not None
        
        # Timestamps should be in order
        assert execution.created_at <= execution.started_at
        assert execution.started_at <= execution.finished_at
    
    def test_workflow_is_terminal(self, db_session, workflow_0a_happy_path):
        """Test that workflow is in terminal state after execution."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        assert execution.is_terminal
    
    def test_step_executions_have_timestamps(self, db_session, workflow_0a_happy_path):
        """Test that all step executions have lifecycle timestamps."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "data": "test"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        for step_exec in step_executions:
            assert step_exec.created_at is not None
            assert step_exec.started_at is not None
            assert step_exec.finished_at is not None
