"""
Integration test for canonical workflows.

This test validates that both canonical workflows (0A and 0B) are properly
wired into the executor and can execute correctly.
"""

from app.models.workflow_execution import WorkflowExecutionStatus
from app.models.step_execution import StepExecution, StepExecutionStatus
from app.executor import LinearExecutor


class TestCanonicalWorkflowsIntegration:
    """Integration tests for canonical workflows."""
    
    def test_both_workflows_execute_correctly(self, db_session, workflow_0a_happy_path, workflow_0b_failure_path):
        """Test that both canonical workflows execute correctly in the same session."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        # Execute Workflow 0A (happy path)
        execution_0a = executor.execute(workflow_0a_happy_path, trigger_input)
        assert execution_0a.status == WorkflowExecutionStatus.SUCCESS
        
        # Execute Workflow 0B (failure path)
        execution_0b = executor.execute(workflow_0b_failure_path, trigger_input)
        assert execution_0b.status == WorkflowExecutionStatus.FAILED
    
    def test_workflows_are_isolated(self, db_session, workflow_0a_happy_path, workflow_0b_failure_path):
        """Test that workflow executions are isolated from each other."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        # Execute both workflows
        execution_0a = executor.execute(workflow_0a_happy_path, trigger_input)
        execution_0b = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Get step executions for each workflow
        steps_0a = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution_0a.id
        ).all()
        steps_0b = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution_0b.id
        ).all()
        
        # Workflow 0A should have 3 step executions (all succeed)
        assert len(steps_0a) == 3
        assert all(s.status == StepExecutionStatus.SUCCESS for s in steps_0a)
        
        # Workflow 0B should have 2 step executions (stops at failure)
        assert len(steps_0b) == 2
        assert steps_0b[0].status == StepExecutionStatus.SUCCESS
        assert steps_0b[1].status == StepExecutionStatus.FAILED
    
    def test_canonical_workflows_are_reusable(self, db_session, workflow_0a_happy_path):
        """Test that canonical workflows can be executed multiple times."""
        executor = LinearExecutor(db_session)
        
        # Execute the same workflow twice
        execution1 = executor.execute(workflow_0a_happy_path, {"run": 1})
        execution2 = executor.execute(workflow_0a_happy_path, {"run": 2})
        
        # Both should succeed
        assert execution1.status == WorkflowExecutionStatus.SUCCESS
        assert execution2.status == WorkflowExecutionStatus.SUCCESS
        
        # They should be different executions
        assert execution1.id != execution2.id
