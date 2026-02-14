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


def seed_ai_summarizer_workflow() -> None:
    session = SessionLocal()
    try:
        workflow = Workflow(
            name="Workflow - AI Summarizer",
            version=1,
            created_by="demo_user",
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)

        # Step 1: Manual input (expects {"text": "..."} )
        step1 = Step(
            workflow_id=workflow.id,
            type=StepType.MANUAL,
            config={
                "description": "Provide text to summarize"
            },
            order=1,
        )
        session.add(step1)

        # Step 2: AI summarize (mock provider by default)
        step2 = Step(
            workflow_id=workflow.id,
            type=StepType.AI,
            config={
                "description": "Summarize the input text",
                "provider": "mock",
                "model": "mock-1",
                "prompt_template": "Summarize: {text}",
                "prompt_id": "summarize_v1",
                "prompt_version": "1.0",
            },
            order=2,
        )
        session.add(step2)

        # Step 3: Persist summary to file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, "ai_summaries.txt")
        step3 = Step(
            workflow_id=workflow.id,
            type=StepType.STORAGE,
            config={
                "description": "Append summary to local file",
                "path": output_path,
                "handler": "file_append",
            },
            order=3,
        )
        session.add(step3)

        session.commit()
        print("✅ Created 'Workflow - AI Summarizer'")
        print(f"   Output file: {output_path}")
    except Exception as exc:
        print(f"❌ Error seeding workflow: {exc}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed_ai_summarizer_workflow()
