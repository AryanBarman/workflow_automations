import pytest

from app.executor.linear_executor import LinearExecutor
from app.models.workflow import Workflow
from app.models.step import Step, StepType
from app.models.step_execution import StepExecution


def test_ai_step_metadata_persisted(db_session):
    workflow = Workflow(name="Workflow - AI Metadata Test", version=1, created_by="test")
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)

    step = Step(
        workflow_id=workflow.id,
        type=StepType.AI,
        config={
            "provider": "mock",
            "model": "mock-1",
            "prompt_template": "Summarize: {text}",
            "prompt_id": "summarize_v1",
            "prompt_version": "1.0",
        },
        order=1,
    )
    db_session.add(step)
    db_session.commit()

    executor = LinearExecutor(db_session)
    execution = executor.execute(workflow, {"text": "Hello world"})

    step_exec = db_session.query(StepExecution).filter_by(workflow_execution_id=execution.id).first()
    assert step_exec is not None
    assert step_exec.step_metadata is not None
    assert step_exec.step_metadata["prompt_id"] == "summarize_v1"
    assert step_exec.step_metadata["prompt_version"] == "1.0"
    assert step_exec.step_metadata["model"] == "mock-1"
    assert step_exec.step_metadata["provider"] == "mock"
