from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import engine
from models import UserTaskInfo

router = APIRouter(prefix="/user-tasks", tags=["UserTaskInfo"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=UserTaskInfo)
def create_task_info(task: UserTaskInfo, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.get("/", response_model=List[UserTaskInfo])
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(select(UserTaskInfo)).all()
