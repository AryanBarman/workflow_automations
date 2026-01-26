"""
Unit tests for Step Lifecycle Logging - Task 0.5.2

Tests validate that ExecutionLog entries are created at step lifecycle events:
1. When step starts (transitions to RUNNING)
2. When step completes successfully (transitions to SUCCESS)
3. When step fails (transitions to FAILED)

Note: These tests filter for step-level logs only (step_execution_id is not None)
to exclude workflow-level logs added in Task 0.5.3.
"""

from app.models import ExecutionLog, StepExecutionStatus
from app.executor import LinearExecutor


class TestStepLifecycleLogging:
    """Test that logs are created during step lifecycle events."""
    
    def test_log_created_when_step_starts(self, db_session, workflow_0a_happy_path):
        """Test that log is created when step transitions to RUNNING."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query all logs
        logs = db_session.query(ExecutionLog).all()
        
        # Should have logs for "Step started"
        started_logs = [log for log in logs if "Step started" in log.message]
        assert len(started_logs) == 3  # 3 steps in workflow 0A
    
    def test_log_created_when_step_succeeds(self, db_session, workflow_0a_happy_path):
        """Test that log is created when step transitions to SUCCESS."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query all logs
        logs = db_session.query(ExecutionLog).all()
        
        # Should have logs for "Step completed successfully" (not "Workflow execution completed")
        success_logs = [log for log in logs if "Step completed successfully" in log.message]
        assert len(success_logs) == 3  # All 3 steps succeed in workflow 0A
    
    def test_log_created_when_step_fails(self, db_session, workflow_0b_failure_path):
        """Test that log is created when step transitions to FAILED."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Query all logs
        logs = db_session.query(ExecutionLog).all()
        
        # Should have log for "Step failed"
        failed_logs = [log for log in logs if "Step failed" in log.message]
        assert len(failed_logs) == 1  # Only step 2 fails in workflow 0B
    
    def test_logs_linked_to_step_execution(self, db_session, workflow_0a_happy_path):
        """Test that step logs are properly linked to StepExecution."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query step-level logs only (step_execution_id is not None)
        step_logs = [log for log in db_session.query(ExecutionLog).all() if log.step_execution_id is not None]
        
        # All step logs should have step_execution_id
        assert len(step_logs) > 0  # Should have step logs
        for log in step_logs:
            assert log.step_execution_id is not None
    
    def test_log_metadata_contains_step_info(self, db_session, workflow_0a_happy_path):
        """Test that step log metadata contains step type and status."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query step-level logs only (step_execution_id is not None)
        step_logs = [log for log in db_session.query(ExecutionLog).all() if log.step_execution_id is not None]
        
        # All step logs should have metadata with step_type and status
        for log in step_logs:
            assert log.log_metadata is not None
            assert "step_type" in log.log_metadata
            assert "status" in log.log_metadata
    
    def test_workflow_0a_creates_six_step_logs(self, db_session, workflow_0a_happy_path):
        """Test that Workflow 0A creates 6 step logs (2 per step: start + success)."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0a_happy_path, trigger_input)
        
        # Query step-level logs only (step_execution_id is not None)
        step_logs = [log for log in db_session.query(ExecutionLog).all() if log.step_execution_id is not None]
        
        # 3 steps × 2 logs each (started + completed) = 6 step logs
        assert len(step_logs) == 6
    
    def test_workflow_0b_creates_four_step_logs(self, db_session, workflow_0b_failure_path):
        """Test that Workflow 0B creates 4 step logs (step1: start+success, step2: start+fail)."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Query step-level logs only (step_execution_id is not None)
        step_logs = [log for log in db_session.query(ExecutionLog).all() if log.step_execution_id is not None]
        
        # Step 1: started + completed = 2 logs
        # Step 2: started + failed = 2 logs
        # Total = 4 step logs
        assert len(step_logs) == 4
    
    def test_failed_step_log_contains_error(self, db_session, workflow_0b_failure_path):
        """Test that failed step log contains error information in metadata."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_0b_failure_path, trigger_input)
        
        # Query failed logs
        logs = db_session.query(ExecutionLog).all()
        failed_logs = [log for log in logs if "Step failed" in log.message]
        
        # Failed log should have error in metadata
        assert len(failed_logs) == 1
        assert "error" in failed_logs[0].log_metadata
        assert "FORCED_FAILURE" in failed_logs[0].log_metadata["error"]
