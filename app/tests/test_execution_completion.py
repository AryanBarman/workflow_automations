"""
Unit tests for Workflow Execution Completion - Task 0.3.5

Tests validate:
1. Workflow completes with SUCCESS when all steps succeed
2. Workflow completes with FAILED when any step fails
3. finished_at timestamp is set on completion
4. Workflow is in terminal state after completion
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.workflow import Workflow
from app.models.step import Step, StepType
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.models.step_execution import StepExecution, StepExecutionStatus
from app.executor import LinearExecutor


# Test database setup
@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create tables
    Workflow.__table__.create(engine, checkfirst=True)
    Step.__table__.create(engine, checkfirst=True)
    WorkflowExecution.__table__.create(engine, checkfirst=True)
    StepExecution.__table__.create(engine, checkfirst=True)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def success_workflow(db_session):
    """Create a workflow with steps that will all succeed."""
    workflow = Workflow(
        name="Success Workflow",
        version=1,
        created_by="test_user"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    
    # Create steps: Input → Transform (both succeed)
    step1 = Step(
        workflow_id=workflow.id,
        type=StepType.MANUAL,  # InputStep - succeeds
        config={},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.LOGIC,  # TransformStep - succeeds
        config={},
        order=2
    )
    
    db_session.add_all([step1, step2])
    db_session.commit()
    return workflow


@pytest.fixture
def failure_workflow(db_session):
    """Create a workflow with a step that will fail."""
    workflow = Workflow(
        name="Failure Workflow",
        version=1,
        created_by="test_user"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    
    # Create steps: Input → Fail
    step1 = Step(
        workflow_id=workflow.id,
        type=StepType.MANUAL,  # InputStep - succeeds
        config={},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.API,  # FailStep - fails
        config={},
        order=2
    )
    
    db_session.add_all([step1, step2])
    db_session.commit()
    return workflow


class TestWorkflowCompletionSuccess:
    """Test workflow completion when all steps succeed."""
    
    def test_workflow_completes_with_success(self, db_session, success_workflow):
        """Test that workflow transitions to SUCCESS when all steps succeed."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        assert execution.status == WorkflowExecutionStatus.SUCCESS
    
    def test_workflow_is_terminal_after_success(self, db_session, success_workflow):
        """Test that workflow is in terminal state after success."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        assert execution.is_terminal
    
    def test_finished_at_set_on_success(self, db_session, success_workflow):
        """Test that finished_at timestamp is set on success."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        assert execution.finished_at is not None
    
    def test_success_workflow_has_all_steps_succeeded(self, db_session, success_workflow):
        """Test that all steps have SUCCESS status when workflow succeeds."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        # All steps should be SUCCESS
        assert all(step_exec.status == StepExecutionStatus.SUCCESS for step_exec in step_executions)


class TestWorkflowCompletionFailure:
    """Test workflow completion when any step fails."""
    
    def test_workflow_completes_with_failed(self, db_session, failure_workflow):
        """Test that workflow transitions to FAILED when any step fails."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(failure_workflow, trigger_input)
        
        assert execution.status == WorkflowExecutionStatus.FAILED
    
    def test_workflow_is_terminal_after_failure(self, db_session, failure_workflow):
        """Test that workflow is in terminal state after failure."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(failure_workflow, trigger_input)
        
        assert execution.is_terminal
    
    def test_finished_at_set_on_failure(self, db_session, failure_workflow):
        """Test that finished_at timestamp is set on failure."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(failure_workflow, trigger_input)
        
        assert execution.finished_at is not None
    
    def test_failed_workflow_has_failed_step(self, db_session, failure_workflow):
        """Test that at least one step has FAILED status when workflow fails."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(failure_workflow, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        # At least one step should be FAILED
        assert any(step_exec.status == StepExecutionStatus.FAILED for step_exec in step_executions)


class TestWorkflowLifecycle:
    """Test complete workflow lifecycle."""
    
    def test_workflow_lifecycle_timestamps(self, db_session, success_workflow):
        """Test that workflow has proper lifecycle timestamps."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        # Should have all lifecycle timestamps
        assert execution.created_at is not None
        assert execution.started_at is not None
        assert execution.finished_at is not None
        
        # Timestamps should be in order
        assert execution.created_at <= execution.started_at
        assert execution.started_at <= execution.finished_at
    
    def test_workflow_cannot_be_modified_after_completion(self, db_session, success_workflow):
        """Test that workflow execution is immutable after completion."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(success_workflow, trigger_input)
        
        # Execution is in terminal state
        assert execution.is_terminal
        
        # Attempting to transition should raise error (enforced by state machine)
        from app.core.exceptions import InvalidStateTransitionError
        with pytest.raises(InvalidStateTransitionError):
            execution.transition_to(WorkflowExecutionStatus.RUNNING)
