import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.workflow import Workflow
from app.models.step import Step, StepType
from app.config import settings

# Setup sync database connection
DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed_ai_guardrail_workflow() -> None:
    session = SessionLocal()
    try:
        workflow = Workflow(
            name="Workflow - AI Guardrail",
            version=1,
            created_by="demo_user",
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)

        # Step 1: Manual input
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.MANUAL,
            config={"description": "Provide text input"},
            order=1,
        )
        session.add(step1)

        # Step 2: AI step with guardrail that should fail
        step2 = Step(
            workflow_id=workflow.id,
            type=StepType.AI,
            config={
                "description": "AI step with output guardrails",
                "provider": "mock",
                "model": "mock-1",
                "prompt_template": "Summarize: {text}",
                "min_text_length": 200,
                "prompt_id": "guardrail_v1",
                "prompt_version": "1.0",
            },
            order=2,
        )
        session.add(step2)

        # Step 3: Persist summary to file (should not run if guardrail fails)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, "ai_guardrail_outputs.txt")
        step3 = Step(
            workflow_id=workflow.id,
            type=StepType.STORAGE,
            config={
                "description": "Persist summary (should not run)",
                "path": output_path,
                "handler": "file_append",
            },
            order=3,
        )
        session.add(step3)

        session.commit()
        print("✅ Created 'Workflow - AI Guardrail'")
        print(f"   Output file (if it ever runs): {output_path}")
    except Exception as exc:
        print(f"❌ Error seeding workflow: {exc}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_ai_guardrail_workflow()
