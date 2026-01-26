"""
Unit tests for Workflow Lifecycle Logging - Task 0.5.3

Tests validate that ExecutionLog entries are created at workflow lifecycle events:
1. When workflow starts (transitions to RUNNING)
2. When workflow completes successfully (transitions to SUCCESS)
3. When workflow fails (transitions to FAILED)
"""

from app.models import ExecutionLog
from app.executor import LinearExecutor


class TestWorkflowLifecycleLogging:
    """Test that logs are created during workflow lifecycle events."""
    
    def test_log_created_when_workflow_starts(self, db_session, workflow_0a_happy_path):
        """Test that log is created when workflow transitions to RUNNING."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query workflow-level logs (step_execution_id is None)
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Should have log for "Workflow execution started"
        started_logs = [log for log in workflow_logs if "started" in log.message]
        assert len(started_logs) == 1
        assert "Workflow execution started" in started_logs[0].message
    
    def test_log_created_when_workflow_succeeds(self, db_session, workflow_0a_happy_path):
        """Test that log is created when workflow transitions to SUCCESS."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Should have log for "completed successfully"
        success_logs = [log for log in workflow_logs if "completed successfully" in log.message]
        assert len(success_logs) == 1
    
    def test_log_created_when_workflow_fails(self, db_session, workflow_0b_failure_path):
        """Test that log is created when workflow transitions to FAILED."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Should have log for "failed"
        failed_logs = [log for log in workflow_logs if "Workflow execution failed" in log.message]
        assert len(failed_logs) == 1
    
    def test_workflow_logs_have_no_step_execution_id(self, db_session, workflow_0a_happy_path):
        """Test that workflow-level logs have step_execution_id = None."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # All workflow logs should have step_execution_id = None
        for log in workflow_logs:
            assert log.step_execution_id is None
    
    def test_workflow_logs_include_workflow_id(self, db_session, workflow_0a_happy_path):
        """Test that workflow logs include workflow_id in metadata."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # All workflow logs should have workflow_id in metadata
        for log in workflow_logs:
            assert log.log_metadata is not None
            assert "workflow_id" in log.log_metadata
    
    def test_workflow_and_step_logs_coexist(self, db_session, workflow_0a_happy_path):
        """Test that both workflow-level and step-level logs are created."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query all logs
        all_logs = db_session.query(ExecutionLog).all()
        
        # Query workflow-level logs (step_execution_id is None)
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Query step-level logs (step_execution_id is not None)
        step_logs = [log for log in all_logs if log.step_execution_id is not None]
        
        # Should have both types of logs
        assert len(workflow_logs) > 0  # At least started + completed
        assert len(step_logs) > 0  # Step logs from Task 0.5.2
        
        # Total logs should be sum of both
        assert len(all_logs) == len(workflow_logs) + len(step_logs)
    
    def test_workflow_0a_creates_two_workflow_logs(self, db_session, workflow_0a_happy_path):
        """Test that Workflow 0A creates 2 workflow logs (started + completed)."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Should have exactly 2 workflow logs: started + completed
        assert len(workflow_logs) == 2
    
    def test_workflow_0b_creates_two_workflow_logs(self, db_session, workflow_0b_failure_path):
        """Test that Workflow 0B creates 2 workflow logs (started + failed)."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Query workflow-level logs
        workflow_logs = db_session.query(ExecutionLog).filter_by(step_execution_id=None).all()
        
        # Should have exactly 2 workflow logs: started + failed
        assert len(workflow_logs) == 2
