from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from database import engine
from models import Tag

router = APIRouter(prefix="/tags", tags=["Tag"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=Tag, status_code=status.HTTP_201_CREATED)
def create_tag(tag: Tag, session: Session = Depends(get_session)):
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag

@router.get("/", response_model=List[Tag])
def list_tags(session: Session = Depends(get_session)):
    return session.exec(select(Tag)).all()

@router.get("/{tag_id}", response_model=Tag)
def get_tag(tag_id: int, session: Session = Depends(get_session)):
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, session: Session = Depends(get_session)):
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    session.delete(tag)
    session.commit()
    return None
