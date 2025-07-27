from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, distinct, func
from database import engine
from models import UserTaskInfo
from datetime import datetime, timedelta

router = APIRouter(prefix="/agents", tags=["Agents"])

def get_session():
    with Session(engine) as session:
        yield session

@router.get("/", response_model=List[str])
def list_agents(session: Session = Depends(get_session)):
    """List all agents in the system"""
    stmt = select(distinct(UserTaskInfo.agent)).where(UserTaskInfo.agent.is_not(None))
    agents = session.exec(stmt).all()
    return list(agents)

@router.get("/count")
def get_agent_count(session: Session = Depends(get_session)):
    """Get the total number of agents"""
    stmt = select(distinct(UserTaskInfo.agent)).where(UserTaskInfo.agent.is_not(None))
    agents = session.exec(stmt).all()
    return {"total_agents": len(agents)}

@router.get("/{agent_name}")
def get_agent_details(agent_name: str, session: Session = Depends(get_session)):
    """Get detailed information about a specific agent"""
    # Check if agent exists
    stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent_name)
    tasks = session.exec(stmt).all()
    
    if not tasks:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "completed"])
    pending_tasks = len([t for t in tasks if t.status in ["assigned", "pending"]])
    
    # Get recent tasks (last 5)
    recent_tasks = sorted(tasks, key=lambda x: x.created_at, reverse=True)[:5]
    
    return {
        "agent_name": agent_name,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
        "recent_tasks": [
            {
                "task_id": task.task_id,
                "status": task.status,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
                "workbench_id": task.workbench_id
            }
            for task in recent_tasks
        ]
    }

@router.post("/{agent_name}/assign-task")
def assign_task_to_agent(
    agent_name: str, 
    task_id: int, 
    workbench_id: int = None,
    session: Session = Depends(get_session)
):
    """Assign a new task to an agent (creates agent if it doesn't exist)"""
    new_task = UserTaskInfo(
        agent=agent_name,
        task_id=task_id,
        status="assigned",
        created_at=datetime.utcnow(),
        workbench_id=workbench_id
    )
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    
    return {
        "message": f"Task {task_id} assigned to agent '{agent_name}'",
        "task": {
            "id": new_task.id,
            "agent": new_task.agent,
            "task_id": new_task.task_id,
            "status": new_task.status,
            "created_at": new_task.created_at,
            "workbench_id": new_task.workbench_id
        }
    }

@router.get("/{agent_name}/tasks")
def get_agent_tasks(agent_name: str, session: Session = Depends(get_session)):
    """Get all tasks for a specific agent"""
    stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent_name)
    tasks = session.exec(stmt).all()
    
    if not tasks:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return [
        {
            "id": task.id,
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "workbench_id": task.workbench_id,
            "process_instance_id": task.process_instance_id
        }
        for task in tasks
    ]