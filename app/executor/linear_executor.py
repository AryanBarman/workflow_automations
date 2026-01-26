"""
Linear Executor - Phase 0, Slice 0.3, Tasks 0.3.3, 0.3.4 & 0.3.5

The core executor that manages workflow execution lifecycle and executes steps sequentially.

For Phase 0, this executor:
- Creates WorkflowExecution records
- Manages state transitions (PENDING → RUNNING → SUCCESS/FAILED)
- Executes steps sequentially
- Creates StepExecution records for each step
- Manages data flow between steps
- Completes workflow execution based on step results
"""

from typing import Any
from sqlalchemy.orm import Session

from app.models import (
    Workflow, WorkflowExecution, WorkflowExecutionStatus,
    Step, StepExecution, StepExecutionStatus, StepType,
    ExecutionLog
)
from app.core.executor_contract import ExecutionContext, StepExecutor
from app.steps import InputStep, TransformStep, PersistStep, FailStep


class LinearExecutor:
    """
    LinearExecutor - Manages workflow execution lifecycle and step execution.
    
    This is the core executor for Phase 0. It:
    1. Accepts a workflow definition and trigger input
    2. Creates a WorkflowExecution in PENDING state
    3. Transitions to RUNNING
    4. Executes steps sequentially
    5. Creates StepExecution records for each step
    6. Manages data flow between steps
    7. Stops on first failure
    8. Completes workflow execution (SUCCESS or FAILED)
    
    Design principles:
    - Boring and simple
    - Depends only on the Step Executor Contract
    - Synchronous (Phase 0 is linear)
    - No retry logic (Phase 1)
    - No validation (Phase 2)
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the executor with a database session.
        
        Args:
            db_session: SQLAlchemy session for persistence
        """
        self.db_session = db_session
    
    def execute(self, workflow: Workflow, trigger_input: Any, trigger_source: str = "manual") -> WorkflowExecution:
        """
        Execute a workflow - create execution, run steps sequentially, complete execution.
        
        This method:
        1. Creates a WorkflowExecution in PENDING state
        2. Persists it to the database
        3. Transitions to RUNNING
        4. Executes steps sequentially
        5. Completes workflow execution (SUCCESS or FAILED)
        6. Returns the execution
        
        Args:
            workflow: The workflow definition to execute
            trigger_input: The input data that triggered this execution
            trigger_source: How this execution was triggered (default: "manual")
            
        Returns:
            WorkflowExecution: The completed execution record (in terminal state)
        """
        # Step 1: Create WorkflowExecution in PENDING state
        workflow_execution = WorkflowExecution(
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            status=WorkflowExecutionStatus.PENDING,
            trigger_source=trigger_source
        )
        
        # Step 2: Persist to database
        self.db_session.add(workflow_execution)
        self.db_session.commit()
        self.db_session.refresh(workflow_execution)
        
        # Step 3: Transition to RUNNING
        workflow_execution.transition_to(WorkflowExecutionStatus.RUNNING)
        self.db_session.commit()
        self.db_session.refresh(workflow_execution)
        
        # Log: Workflow execution started
        log_workflow_started = ExecutionLog(
            step_execution_id=None,  # Workflow-level log
            message=f"Workflow execution started: {workflow.name}",
            log_metadata={"workflow_id": str(workflow.id), "status": "RUNNING"}
        )
        self.db_session.add(log_workflow_started)
        self.db_session.commit()
        
        # Step 4: Execute steps sequentially
        self._execute_steps(workflow_execution, workflow, trigger_input)
        
        # Step 5: Complete workflow execution
        self._complete_workflow_execution(workflow_execution)
        
        return workflow_execution
    
    def _execute_steps(self, workflow_execution: WorkflowExecution, workflow: Workflow, trigger_input: Any) -> None:
        """
        Execute all steps in the workflow sequentially.
        
        This method:
        - Iterates through steps in order
        - Creates StepExecution for each step
        - Executes step using the contract
        - Manages state transitions
        - Passes output from step N to step N+1
        - Stops on first failure
        
        Args:
            workflow_execution: The workflow execution record
            workflow: The workflow definition
            trigger_input: The initial input data
        """
        # Get steps ordered by their order field (query directly to avoid relationship issues)
        steps = self.db_session.query(Step).filter_by(workflow_id=workflow.id).order_by(Step.order).all()
        
        # Initialize current input with trigger input
        current_input = trigger_input
        
        # Execute each step sequentially
        for step in steps:
            # Create StepExecution in PENDING state
            step_execution = StepExecution(
                workflow_execution_id=workflow_execution.id,
                step_id=step.id,
                status=StepExecutionStatus.PENDING,
                input=current_input if isinstance(current_input, dict) else {"value": current_input}
            )
            
            self.db_session.add(step_execution)
            self.db_session.commit()
            self.db_session.refresh(step_execution)
            
            # Transition to RUNNING
            step_execution.transition_to(StepExecutionStatus.RUNNING)
            self.db_session.commit()
            
            # Log: Step started
            log_started = ExecutionLog(
                step_execution_id=str(step_execution.id),
                message=f"Step started: {step.type.value}",
                log_metadata={"step_type": step.type.value, "status": "RUNNING"}
            )
            self.db_session.add(log_started)
            self.db_session.commit()
            
            # Create execution context
            context = ExecutionContext(
                workflow_execution_id=workflow_execution.id,
                step_execution_id=step_execution.id,
                workflow_id=workflow.id,
                step_id=step.id,
                trigger_input=trigger_input
            )
            
            # Instantiate and execute the step
            step_instance = self._instantiate_step(step)
            result = step_instance.execute(current_input, context)
            
            # Handle result based on status
            if result.status == "success":
                # Transition to SUCCESS
                step_execution.transition_to(StepExecutionStatus.SUCCESS)
                step_execution.output = result.output
                current_input = result.output  # Pass output to next step
                
                # Log: Step completed successfully
                log_success = ExecutionLog(
                    step_execution_id=str(step_execution.id),
                    message=f"Step completed successfully: {step.type.value}",
                    log_metadata={"step_type": step.type.value, "status": "SUCCESS"}
                )
                self.db_session.add(log_success)
                
            else:  # failure
                # Transition to FAILED
                step_execution.transition_to(StepExecutionStatus.FAILED)
                if result.error:
                    step_execution.error = f"{result.error.code}: {result.error.message}"
                
                # Log: Step failed
                error_msg = f"{result.error.code}: {result.error.message}" if result.error else "Unknown error"
                log_failed = ExecutionLog(
                    step_execution_id=str(step_execution.id),
                    message=f"Step failed: {step.type.value}",
                    log_metadata={
                        "step_type": step.type.value,
                        "status": "FAILED",
                        "error": error_msg
                    }
                )
                self.db_session.add(log_failed)
                
                # Persist and stop execution
                self.db_session.commit()
                break  # Stop on first failure
            
            # Persist step execution
            self.db_session.commit()
            self.db_session.refresh(step_execution)
    
    def _instantiate_step(self, step: Step) -> StepExecutor:
        """
        Instantiate the appropriate step class based on step type.
        
        For Phase 0, we use simple if/elif mapping.
        In later phases, this could use a factory pattern.
        
        Args:
            step: The step definition
            
        Returns:
            An instance of the appropriate step class
            
        Raises:
            ValueError: If step type is not recognized
        """
        if step.type == StepType.MANUAL:
            return InputStep()
        elif step.type == StepType.LOGIC:
            return TransformStep()
        elif step.type == StepType.STORAGE:
            return PersistStep()
        elif step.type == StepType.AI:
            # For Phase 0, AI steps not implemented yet
            return FailStep()
        elif step.type == StepType.API:
            # For Phase 0, API steps not implemented yet
            return FailStep()
        else:
            raise ValueError(f"Unknown step type: {step.type}")
    
    def _complete_workflow_execution(self, workflow_execution: WorkflowExecution) -> None:
        """
        Complete the workflow execution by transitioning to terminal state.
        
        This method:
        - Queries all StepExecution records for this workflow
        - Checks if any step failed
        - Transitions to FAILED if any step failed
        - Transitions to SUCCESS if all steps succeeded
        - Sets finished_at timestamp via state machine
        
        Args:
            workflow_execution: The workflow execution to complete
        """
        # Query all step executions for this workflow
        step_executions = self.db_session.query(StepExecution).filter_by(
            workflow_execution_id=workflow_execution.id
        ).all()
        
        # Check if any step failed
        any_failed = any(step_exec.status == StepExecutionStatus.FAILED for step_exec in step_executions)
        
        if any_failed:
            # Transition to FAILED
            workflow_execution.transition_to(WorkflowExecutionStatus.FAILED)
            
            # Log: Workflow execution failed
            log_workflow_failed = ExecutionLog(
                step_execution_id=None,  # Workflow-level log
                message="Workflow execution failed",
                log_metadata={"workflow_id": str(workflow_execution.workflow_id), "status": "FAILED"}
            )
            self.db_session.add(log_workflow_failed)
            
        else:
            # All steps succeeded, transition to SUCCESS
            workflow_execution.transition_to(WorkflowExecutionStatus.SUCCESS)
            
            # Log: Workflow execution completed successfully
            log_workflow_success = ExecutionLog(
                step_execution_id=None,  # Workflow-level log
                message="Workflow execution completed successfully",
                log_metadata={"workflow_id": str(workflow_execution.workflow_id), "status": "SUCCESS"}
            )
            self.db_session.add(log_workflow_success)
        
        # Persist final state
        self.db_session.commit()
        self.db_session.refresh(workflow_execution)
