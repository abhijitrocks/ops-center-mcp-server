from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import engine
from models import Tenant

router = APIRouter(prefix="/tenants", tags=["Tenant"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=Tenant, status_code=status.HTTP_201_CREATED)
def create_tenant(tenant: Tenant, session: Session = Depends(get_session)):
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant

@router.get("/", response_model=list[Tenant])
def list_tenants(session: Session = Depends(get_session)):
    return session.exec(select(Tenant)).all()

@router.get("/{tenant_id}", response_model=Tenant)
def get_tenant(tenant_id: int, session: Session = Depends(get_session)):
    t = session.get(Tenant, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t
