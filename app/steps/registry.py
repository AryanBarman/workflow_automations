"""
Step Registry - Centralized step instantiation boundary.

This module isolates step creation logic so new step types can be
added without modifying the executor.
"""

from app.models.step import Step, StepType
from app.core.executor_contract import StepExecutor

from app.steps.input_step import InputStep
from app.steps.transform_step import TransformStep
from app.steps.persist_step import PersistStep
from app.steps.fail_step import FailStep
from app.steps.transient_fail_step import TransientFailStep
from app.steps.http_step import HttpStep
from app.steps.ai_step import AiStep
from app.steps.weather_transform_step import WeatherTransformStep


def create_step(step: Step) -> StepExecutor:
    """
    Instantiate the appropriate step class based on step type/config.

    This is the single boundary for step creation.
    """
    instance: StepExecutor | None = None

    if step.type == StepType.MANUAL:
        instance = InputStep()
    elif step.type == StepType.LOGIC:
        if step.config.get("handler") == "weather_formatter":
            instance = WeatherTransformStep()
        else:
            instance = TransformStep()
    elif step.type == StepType.STORAGE:
        instance = PersistStep()
    elif step.type == StepType.AI:
        instance = AiStep(config=step.config)
    elif step.type == StepType.API:
        handler = step.config.get("handler")
        if handler == "http":
            instance = HttpStep(config=step.config)
        else:
            instance = TransientFailStep()
    else:
        raise ValueError(f"Unknown step type: {step.type}")

    # Inject config if the step didn't set it.
    if not hasattr(instance, "config"):
        instance.config = step.config
    if not getattr(instance, "config", None):
        instance.config = step.config

    return instance
