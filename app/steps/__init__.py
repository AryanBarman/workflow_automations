"""
Canonical Phase 0 Step Types

This package contains the four canonical step implementations for Phase 0:
- InputStep: Pass-through step (manual input)
- TransformStep: Pure logic transformation
- PersistStep: Side-effect step (storage simulation)
- FailStep: Forced failure step (for testing)

All steps implement the StepExecutor contract.
"""

from app.steps.input_step import InputStep
from app.steps.transform_step import TransformStep
from app.steps.persist_step import PersistStep
from app.steps.fail_step import FailStep
from app.steps.transient_fail_step import TransientFailStep

__all__ = [
    "InputStep",
    "TransformStep",
    "PersistStep",
    "FailStep",
    "TransientFailStep",
]
