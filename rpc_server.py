# File: rpc_server.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
from sqlmodel import Session, select
from database import engine
from models import UserTaskInfo, Tag
from datetime import datetime, timedelta

app = FastAPI(title="MCP JSON-RPC Server")

# JSON-RPC 2.0 request model
class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[dict] = {}
    id: Optional[Any] = None

# JSON-RPC 2.0 response model
class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict] = None
    id: Optional[Any] = None

@app.post("/rpc")
async def handle_rpc(request: Request):
    req_data = await request.json()
    rpc_request = JSONRPCRequest(**req_data)
    response = JSONRPCResponse(id=rpc_request.id)

    try:
        method = rpc_request.method
        params = rpc_request.params or {}
        if method == "get_agent_task_count":
            result = get_agent_task_count(**params)
        elif method == "create_agent":
            result = create_agent(**params)
        elif method == "list_all_agents":
            result = list_all_agents(**params)
        elif method == "list_recent_tasks":
            result = list_recent_tasks(**params)
        elif method == "average_completion_time":
            result = average_completion_time(**params)
        elif method == "list_tags":
            result = list_tags(**params)
        elif method == "assign_task":
            result = assign_task(**params)
        elif method == "update_task_status":
            result = update_task_status(**params)
        else:
            response.error = {"code": -32601, "message": "Method not found"}
            return response
        response.result = result
    except Exception as e:
        response.error = {"code": -32000, "message": str(e)}
    return response

# RPC methods

def get_agent_task_count(agent: str, days: int = 3) -> dict:
    with Session(engine) as session:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = select(UserTaskInfo).where(
            UserTaskInfo.agent == agent,
            UserTaskInfo.status == "completed",
            UserTaskInfo.completed_at >= since
        )
        tasks = session.exec(stmt).all()
        return {"agent": agent, "completed_tasks": len(tasks)}


def list_recent_tasks(agent: str, limit: int = 5) -> List[dict]:
    with Session(engine) as session:
        stmt = select(UserTaskInfo).where(
            UserTaskInfo.agent == agent,
            UserTaskInfo.status == "completed"
        ).order_by(UserTaskInfo.completed_at.desc()).limit(limit)
        tasks = session.exec(stmt).all()
        return [task.dict() for task in tasks]


def average_completion_time(agent: str) -> dict:
    with Session(engine) as session:
        stmt = select(UserTaskInfo).where(
            UserTaskInfo.agent == agent,
            UserTaskInfo.status == "completed",
            UserTaskInfo.completed_at.is_not(None)
        )
        tasks = session.exec(stmt).all()
        durations = [
            (task.completed_at - task.created_at).total_seconds()
            for task in tasks if task.completed_at and task.created_at
        ]
        avg_seconds = sum(durations) / len(durations) if durations else 0
        return {"agent": agent, "average_completion_time_seconds": avg_seconds}


def list_tags(tenant_id: int) -> List[dict]:
    with Session(engine) as session:
        stmt = select(Tag).where(Tag.tenant_id == tenant_id)
        tags = session.exec(stmt).all()
        return [tag.dict() for tag in tags]


def assign_task(agent: str, task_id: int, workbench_id: Optional[int] = None) -> dict:
    new_task = UserTaskInfo(
        agent=agent,
        task_id=task_id,
        status="assigned",
        created_at=datetime.utcnow(),
        workbench_id=workbench_id
    )
    with Session(engine) as session:
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task.dict()


def create_agent(agent_name: str, task_id: int = None, workbench_id: Optional[int] = None) -> dict:
    """Create a new agent by assigning a task to them"""
    if task_id is None:
        # Generate a unique task_id if not provided
        import random
        task_id = random.randint(10000, 99999)
    
    new_task = UserTaskInfo(
        agent=agent_name,
        task_id=task_id,
        status="assigned",
        created_at=datetime.utcnow(),
        workbench_id=workbench_id
    )
    
    with Session(engine) as session:
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return {
            "message": f"Agent '{agent_name}' created successfully",
            "agent": agent_name,
            "task_id": task_id,
            "status": "assigned"
        }


def list_all_agents() -> List[dict]:
    """List all agents in the system with their basic stats"""
    with Session(engine) as session:
        stmt = select(distinct(UserTaskInfo.agent)).where(UserTaskInfo.agent.is_not(None))
        agents = session.exec(stmt).all()
        
        agent_stats = []
        for agent in agents:
            # Get task counts for each agent
            agent_tasks_stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent)
            tasks = session.exec(agent_tasks_stmt).all()
            
            completed_count = len([t for t in tasks if t.status == "completed"])
            total_count = len(tasks)
            
            agent_stats.append({
                "agent_name": agent,
                "total_tasks": total_count,
                "completed_tasks": completed_count,
                "completion_rate": round(completed_count / total_count * 100, 2) if total_count > 0 else 0
            })
        
        return agent_stats


def update_task_status(task_id: int, agent: Optional[str] = None, status: str = "completed") -> dict:
    with Session(engine) as session:
        stmt = select(UserTaskInfo).where(UserTaskInfo.task_id == task_id)
        task = session.exec(stmt).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if agent:
            task.agent = agent
        task.status = status
        if status == "completed":
            task.completed_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task.dict()
