"""
Unit tests for LinearExecutor Sequential Step Execution - Task 0.3.4

Tests validate:
1. Steps are executed sequentially
2. StepExecution records are created
3. Data flows between steps
4. Execution stops on failure
5. State transitions work correctly
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
    
    # Create only the tables we need
    Workflow.__table__.create(engine, checkfirst=True)
    Step.__table__.create(engine, checkfirst=True)
    WorkflowExecution.__table__.create(engine, checkfirst=True)
    StepExecution.__table__.create(engine, checkfirst=True)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def workflow_with_steps(db_session):
    """Create a workflow with three steps for testing."""
    # Create workflow
    workflow = Workflow(
        name="Test Workflow with Steps",
        version=1,
        created_by="test_user"
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    
    # Create steps: Input → Transform → Fail
    step1 = Step(
        workflow_id=workflow.id,
        type=StepType.MANUAL,  # Maps to InputStep
        config={},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.LOGIC,  # Maps to TransformStep
        config={},
        order=2
    )
    step3 = Step(
        workflow_id=workflow.id,
        type=StepType.API,  # Maps to FailStep for Phase 0
        config={},
        order=3
    )
    
    db_session.add_all([step1, step2, step3])
    db_session.commit()
    
    # Manually load steps to avoid relationship issues
    workflow.steps = db_session.query(Step).filter_by(workflow_id=workflow.id).all()
    return workflow


@pytest.fixture
def workflow_with_success_steps(db_session):
    """Create a workflow with steps that will succeed."""
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
        type=StepType.MANUAL,
        config={},
        order=1
    )
    step2 = Step(
        workflow_id=workflow.id,
        type=StepType.LOGIC,
        config={},
        order=2
    )
    
    db_session.add_all([step1, step2])
    db_session.commit()
    
    # Manually load steps to avoid relationship issues
    workflow.steps = db_session.query(Step).filter_by(workflow_id=workflow.id).all()
    return workflow


class TestSequentialStepExecution:
    """Test that executor executes steps sequentially."""
    
    def test_executor_creates_step_executions(self, db_session, workflow_with_success_steps):
        """Test that executor creates StepExecution for each step."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        # Query step executions
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        assert len(step_executions) == 2  # Two steps
    
    def test_executor_executes_steps_in_order(self, db_session, workflow_with_success_steps):
        """Test that steps are executed in order."""
        executor = LinearExecutor(db_session)
        trigger_input = {"initial": "value"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        # Get step executions in creation order
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # First step should be MANUAL (InputStep)
        step1_def = db_session.query(Step).filter_by(id=step_executions[0].step_id).first()
        assert step1_def.type == StepType.MANUAL
        
        # Second step should be LOGIC (TransformStep)
        step2_def = db_session.query(Step).filter_by(id=step_executions[1].step_id).first()
        assert step2_def.type == StepType.LOGIC
    
    def test_step_executions_transition_to_success(self, db_session, workflow_with_success_steps):
        """Test that successful steps transition to SUCCESS."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        # All steps should be SUCCESS
        for step_exec in step_executions:
            assert step_exec.status == StepExecutionStatus.SUCCESS
    
    def test_step_executions_have_timestamps(self, db_session, workflow_with_success_steps):
        """Test that step executions have proper timestamps."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        for step_exec in step_executions:
            assert step_exec.created_at is not None
            assert step_exec.started_at is not None
            assert step_exec.finished_at is not None


class TestDataFlowBetweenSteps:
    """Test that data flows correctly between steps."""
    
    def test_output_passed_to_next_step(self, db_session, workflow_with_success_steps):
        """Test that output from step N becomes input to step N+1."""
        executor = LinearExecutor(db_session)
        trigger_input = {"initial": "value"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # First step (InputStep) should have trigger_input as input
        assert step_executions[0].input == trigger_input
        
        # Second step (TransformStep) should have first step's output as input
        # TransformStep adds fields to the input
        assert step_executions[1].input == step_executions[0].output
    
    def test_transform_step_modifies_data(self, db_session, workflow_with_success_steps):
        """Test that TransformStep actually transforms data."""
        executor = LinearExecutor(db_session)
        trigger_input = {"original": "data"}
        
        execution = executor.execute(workflow_with_success_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # Second step is TransformStep - should add "processed" field
        transform_output = step_executions[1].output
        assert "processed" in transform_output
        assert transform_output["processed"] is True


class TestFailureHandling:
    """Test that executor handles step failures correctly."""
    
    def test_execution_stops_on_failure(self, db_session, workflow_with_steps):
        """Test that execution stops when a step fails."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        # This workflow has 3 steps: Input → Transform → Fail
        # Should stop at the third step (FailStep)
        execution = executor.execute(workflow_with_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).all()
        
        # Should have 3 step executions (all steps attempted)
        assert len(step_executions) == 3
        
        # First two should succeed, third should fail
        step_execs_ordered = sorted(step_executions, key=lambda x: x.created_at)
        assert step_execs_ordered[0].status == StepExecutionStatus.SUCCESS
        assert step_execs_ordered[1].status == StepExecutionStatus.SUCCESS
        assert step_execs_ordered[2].status == StepExecutionStatus.FAILED
    
    def test_failed_step_has_error(self, db_session, workflow_with_steps):
        """Test that failed step has error message."""
        executor = LinearExecutor(db_session)
        trigger_input = {"test": "data"}
        
        execution = executor.execute(workflow_with_steps, trigger_input)
        
        step_executions = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).order_by(StepExecution.created_at).all()
        
        # Third step should have failed with error
        failed_step = step_executions[2]
        assert failed_step.error is not None
        assert "FORCED_FAILURE" in failed_step.error


class TestStepInstantiation:
    """Test that steps are instantiated correctly."""
    
    def test_manual_step_maps_to_input_step(self, db_session):
        """Test that MANUAL type maps to InputStep."""
        workflow = Workflow(name="Test", version=1, created_by="test")
        db_session.add(workflow)
        db_session.commit()
        
        step = Step(workflow_id=workflow.id, type=StepType.MANUAL, config={}, order=1)
        db_session.add(step)
        db_session.commit()
        db_session.refresh(workflow)
        
        executor = LinearExecutor(db_session)
        execution = executor.execute(workflow, {"test": "data"})
        
        step_exec = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).first()
        
        # InputStep passes through, so output == input
        assert step_exec.output == step_exec.input
    
    def test_logic_step_maps_to_transform_step(self, db_session):
        """Test that LOGIC type maps to TransformStep."""
        workflow = Workflow(name="Test", version=1, created_by="test")
        db_session.add(workflow)
        db_session.commit()
        
        step = Step(workflow_id=workflow.id, type=StepType.LOGIC, config={}, order=1)
        db_session.add(step)
        db_session.commit()
        db_session.refresh(workflow)
        
        executor = LinearExecutor(db_session)
        execution = executor.execute(workflow, {"test": "data"})
        
        step_exec = db_session.query(StepExecution).filter_by(
            workflow_execution_id=execution.id
        ).first()
        
        # TransformStep adds "processed" field
        assert "processed" in step_exec.output
        assert step_exec.output["processed"] is True
