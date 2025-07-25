from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from database import engine
from models import UserTaskInfo

router = APIRouter(prefix="/performance", tags=["Performance"])

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/agents/completed")
def completed_by_agent(session: Session = Depends(get_session)):
    stmt = select(UserTaskInfo.agent, func.count().label("completed_tasks")) \
.group_by(UserTaskInfo.agent)
    results = session.exec(stmt).all()
    return [{"agent": r[0], "completed_tasks": r[1]} for r in results]
