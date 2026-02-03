
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "workflow_automation_backend"))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.workflow import Workflow
from app.models.step import Step

def list_workflows():
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        workflows = session.query(Workflow).order_by(Workflow.created_at.desc()).all()
        print(f"Found {len(workflows)} workflows:")
        
        for w in workflows:
            step_count = session.query(func.count(Step.id)).filter(Step.workflow_id == w.id).scalar()
            print(f"  ID: {w.id} | Name: {w.name} | Created: {w.created_at} | Steps: {step_count}")

    finally:
        session.close()

if __name__ == "__main__":
    list_workflows()
