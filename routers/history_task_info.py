from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import engine
from models import HistoryTaskInfo

router = APIRouter(prefix="/history-tasks", tags=["HistoryTaskInfo"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=HistoryTaskInfo)
def create_history(info: HistoryTaskInfo, session: Session = Depends(get_session)):
    session.add(info)
    session.commit()
    session.refresh(info)
    return info

@router.get("/", response_model=List[HistoryTaskInfo])
def list_history(session: Session = Depends(get_session)):
    return session.exec(select(HistoryTaskInfo)).all()
