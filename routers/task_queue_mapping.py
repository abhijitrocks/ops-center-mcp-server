from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from database import engine
from models import TaskQueueMapping

router = APIRouter(prefix="/task-queue-mapping", tags=["TaskQueueMapping"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=TaskQueueMapping, status_code=status.HTTP_201_CREATED)
def create_mapping(mapping: TaskQueueMapping, session: Session = Depends(get_session)):
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping

@router.get("/", response_model=List[TaskQueueMapping])
def list_mappings(session: Session = Depends(get_session)):
    return session.exec(select(TaskQueueMapping)).all()

@router.get("/{mapping_id}", response_model=TaskQueueMapping)
def get_mapping(mapping_id: int, session: Session = Depends(get_session)):
    m = session.get(TaskQueueMapping, mapping_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return m

@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(mapping_id: int, session: Session = Depends(get_session)):
    m = session.get(TaskQueueMapping, mapping_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mapping not found")
    session.delete(m)
    session.commit()
    return None
