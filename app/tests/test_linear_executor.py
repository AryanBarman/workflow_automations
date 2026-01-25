"""
Unit tests for LinearExecutor - Phase 0, Slice 0.3, Task 0.3.3

Tests validate:
1. WorkflowExecution is created in PENDING state
2. Execution transitions to RUNNING
3. Execution is persisted to database
4. Executor returns the execution

Note: These tests use a simplified setup to avoid async complexity.
Full integration tests will be added in Task 0.3.4.
"""

import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.executor import LinearExecutor


# Test database setup
@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create only the tables we need for this test
    WorkflowExecution.__table__.create(engine, checkfirst=True)
    Workflow.__table__.create(engine, checkfirst=True)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_workflow(db_session):
    """Create a sample workflow for testing."""
    workflow = Workflow(
        name="Test Workflow",
        version=1,
        created_by="test_user"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    return workflow


class TestLinearExecutorCore:
    """Test LinearExecutor core functionality."""
    
    def test_executor_creates_workflow_execution(self, db_session, sample_workflow):
        """Test that executor creates a WorkflowExecution."""
        executor = LinearExecutor(db_session)
        trigger_input = {"user_id": "123", "action": "process"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        
        assert execution is not None
        assert isinstance(execution, WorkflowExecution)
        assert execution.id is not None
    
    def test_executor_sets_workflow_reference(self, db_session, sample_workflow):
        """Test that execution references the correct workflow."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        
        assert execution.workflow_id == sample_workflow.id
        assert execution.workflow_version == sample_workflow.version
    
    def test_executor_transitions_to_running(self, db_session, sample_workflow):
        """Test that executor transitions execution to RUNNING."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        
        assert execution.status == WorkflowExecutionStatus.RUNNING
    
    def test_executor_sets_started_at(self, db_session, sample_workflow):
        """Test that started_at is set when transitioning to RUNNING."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        
        assert execution.started_at is not None
    
    def test_executor_persists_execution(self, db_session, sample_workflow):
        """Test that execution is persisted to database."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        execution_id = execution.id
        
        # Query database to verify persistence
        persisted = db_session.query(WorkflowExecution).filter_by(id=execution_id).first()
        
        assert persisted is not None
        assert persisted.id == execution_id
        assert persisted.status == WorkflowExecutionStatus.RUNNING
    
    def test_executor_sets_trigger_source(self, db_session, sample_workflow):
        """Test that trigger source is set correctly."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        # Default trigger source
        execution1 = executor.execute(sample_workflow, trigger_input)
        assert execution1.trigger_source == "manual"
        
        # Custom trigger source
        execution2 = executor.execute(sample_workflow, trigger_input, trigger_source="api")
        assert execution2.trigger_source == "api"
    
    def test_executor_returns_execution(self, db_session, sample_workflow):
        """Test that executor returns the WorkflowExecution."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(sample_workflow, trigger_input)
        
        assert execution is not None
        assert isinstance(execution, WorkflowExecution)
        assert execution.status == WorkflowExecutionStatus.RUNNING
    
    def test_executor_creates_multiple_executions(self, db_session, sample_workflow):
        """Test that executor can create multiple executions for same workflow."""
        executor = LinearExecutor(db_session)
        
        execution1 = executor.execute(sample_workflow, {"run": 1})
        execution2 = executor.execute(sample_workflow, {"run": 2})
        execution3 = executor.execute(sample_workflow, {"run": 3})
        
        # All should be different executions
        assert execution1.id != execution2.id
        assert execution2.id != execution3.id
        assert execution1.id != execution3.id
        
        # All should reference same workflow
        assert execution1.workflow_id == sample_workflow.id
        assert execution2.workflow_id == sample_workflow.id
        assert execution3.workflow_id == sample_workflow.id


class TestLinearExecutorStateTransitions:
    """Test that executor properly manages state transitions."""
    
    def test_execution_has_lifecycle_timestamps(self, db_session, sample_workflow):
        """Test that execution has proper lifecycle timestamps."""
        executor = LinearExecutor(db_session)
        
        execution = executor.execute(sample_workflow, {})
        
        # Should have created_at (from model default)
        assert execution.created_at is not None
        
        # Should have started_at (from transition to RUNNING)
        assert execution.started_at is not None
        
        # Should NOT have finished_at (not terminal yet)
        assert execution.finished_at is None
    
    def test_execution_not_terminal(self, db_session, sample_workflow):
        """Test that RUNNING execution is not terminal."""
        executor = LinearExecutor(db_session)
        
        execution = executor.execute(sample_workflow, {})
        
        assert execution.status == WorkflowExecutionStatus.RUNNING
        assert not execution.is_terminal

