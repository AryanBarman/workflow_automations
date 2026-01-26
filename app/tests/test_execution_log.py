"""
Unit tests for ExecutionLog model - Task 0.5.1

Tests validate:
1. ExecutionLog can be created
2. Relationship to StepExecution works
3. log_metadata can store JSON data
4. Logs can be queried for a step
"""

import pytest
from datetime import datetime

from app.models import ExecutionLog, StepExecution, WorkflowExecution, Workflow, Step, StepType, StepExecutionStatus, WorkflowExecutionStatus


class TestExecutionLogModel:
    """Test ExecutionLog model."""
    
    def test_create_execution_log(self, db_session):
        """Test that ExecutionLog can be created."""
        log = ExecutionLog(
            message="Test log message",
            timestamp=datetime.utcnow()
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.message == "Test log message"
        assert log.timestamp is not None
    
    def test_log_with_metadata(self, db_session):
        """Test that log_metadata can store JSON data."""
        log = ExecutionLog(
            message="Test with metadata",
            log_metadata={"key": "value", "count": 42}
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.log_metadata is not None
        assert log.log_metadata["key"] == "value"
        assert log.log_metadata["count"] == 42
    
    def test_log_linked_to_step_execution(self, db_session, workflow_0a_happy_path):
        """Test that ExecutionLog can be linked to StepExecution."""
        # Create a workflow execution
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_0a_happy_path.id,
            workflow_version=workflow_0a_happy_path.version,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="test"
        )
        db_session.add(workflow_execution)
        db_session.commit()
        db_session.refresh(workflow_execution)
        
        # Get first step
        steps = db_session.query(Step).filter_by(workflow_id=workflow_0a_happy_path.id).order_by(Step.order).all()
        
        # Create step execution
        step_execution = StepExecution(
            workflow_execution_id=workflow_execution.id,
            step_id=steps[0].id,
            status=StepExecutionStatus.PENDING,
            input={"test": "data"}
        )
        db_session.add(step_execution)
        db_session.commit()
        db_session.refresh(step_execution)
        
        # Create log linked to step execution
        log = ExecutionLog(
            step_execution_id=step_execution.id,
            message="Step started",
            log_metadata={"step_type": "MANUAL"}
        )
        db_session.add(log)
        db_session.commit()
        
        assert log.step_execution_id == step_execution.id
        assert log.step_execution is not None
        assert log.step_execution.id == step_execution.id
    
    def test_query_logs_for_step(self, db_session, workflow_0a_happy_path):
        """Test that logs can be queried for a specific step execution."""
        # Create workflow execution
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_0a_happy_path.id,
            workflow_version=workflow_0a_happy_path.version,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="test"
        )
        db_session.add(workflow_execution)
        db_session.commit()
        db_session.refresh(workflow_execution)
        
        # Get first step
        steps = db_session.query(Step).filter_by(workflow_id=workflow_0a_happy_path.id).order_by(Step.order).all()
        
        # Create step execution
        step_execution = StepExecution(
            workflow_execution_id=workflow_execution.id,
            step_id=steps[0].id,
            status=StepExecutionStatus.PENDING,
            input={"test": "data"}
        )
        db_session.add(step_execution)
        db_session.commit()
        db_session.refresh(step_execution)
        
        # Create multiple logs
        log1 = ExecutionLog(
            step_execution_id=step_execution.id,
            message="Step started"
        )
        log2 = ExecutionLog(
            step_execution_id=step_execution.id,
            message="Processing data"
        )
        log3 = ExecutionLog(
            step_execution_id=step_execution.id,
            message="Step completed"
        )
        
        db_session.add_all([log1, log2, log3])
        db_session.commit()
        
        # Query logs for this step
        logs = db_session.query(ExecutionLog).filter_by(
            step_execution_id=step_execution.id
        ).order_by(ExecutionLog.timestamp).all()
        
        assert len(logs) == 3
        assert logs[0].message == "Step started"
        assert logs[1].message == "Processing data"
        assert logs[2].message == "Step completed"
    
    def test_step_execution_has_logs_relationship(self, db_session, workflow_0a_happy_path):
        """Test that StepExecution has logs relationship."""
        # Create workflow execution
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_0a_happy_path.id,
            workflow_version=workflow_0a_happy_path.version,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source="test"
        )
        db_session.add(workflow_execution)
        db_session.commit()
        db_session.refresh(workflow_execution)
        
        # Get first step
        steps = db_session.query(Step).filter_by(workflow_id=workflow_0a_happy_path.id).order_by(Step.order).all()
        
        # Create step execution
        step_execution = StepExecution(
            workflow_execution_id=workflow_execution.id,
            step_id=steps[0].id,
            status=StepExecutionStatus.PENDING,
            input={"test": "data"}
        )
        db_session.add(step_execution)
        db_session.commit()
        db_session.refresh(step_execution)
        
        # Create logs
        log1 = ExecutionLog(step_execution_id=step_execution.id, message="Log 1")
        log2 = ExecutionLog(step_execution_id=step_execution.id, message="Log 2")
        
        db_session.add_all([log1, log2])
        db_session.commit()
        db_session.refresh(step_execution)
        
        # Access logs via relationship
        assert len(step_execution.logs) == 2
        assert step_execution.logs[0].message in ["Log 1", "Log 2"]
        assert step_execution.logs[1].message in ["Log 1", "Log 2"]
