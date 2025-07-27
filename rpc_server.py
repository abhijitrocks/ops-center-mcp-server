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
        elif method == "list_agents":
            result = list_agents(**params)
        elif method == "get_agent_info":
            result = get_agent_info(**params)
        elif method == "get_agent_stats":
            result = get_agent_stats(**params)
        elif method == "create_agent":
            result = create_agent(**params)
        elif method == "assign_role":
            result = assign_role(**params)
        elif method == "get_agent_roles":
            result = get_agent_roles(**params)
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


def list_agents(limit: int = 100) -> dict:
    """List all unique agents and their basic info"""
    with Session(engine) as session:
        # Get unique agents from UserTaskInfo
        stmt = select(UserTaskInfo.agent).distinct().limit(limit)
        agents = session.exec(stmt).all()
        
        agent_list = []
        for agent in agents:
            if agent:  # Skip None values
                agent_list.append(agent)
        
        return {
            "total_agents": len(agent_list),
            "agents": agent_list,
            "limit": limit
        }


def get_agent_info(agent: str) -> dict:
    """Get detailed information about a specific agent"""
    with Session(engine) as session:
        # Get all tasks for this agent
        stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent)
        tasks = session.exec(stmt).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        in_progress_tasks = len([t for t in tasks if t.status == "in_progress"])
        assigned_tasks = len([t for t in tasks if t.status == "assigned"])
        
        # Get the most recent task
        recent_stmt = select(UserTaskInfo).where(
            UserTaskInfo.agent == agent
        ).order_by(UserTaskInfo.created_at.desc()).limit(1)
        recent_task = session.exec(recent_stmt).first()
        
        return {
            "agent": agent,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "assigned_tasks": assigned_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "most_recent_task": {
                "task_id": recent_task.task_id if recent_task else None,
                "status": recent_task.status if recent_task else None,
                "created_at": recent_task.created_at.isoformat() if recent_task and recent_task.created_at else None
            } if recent_task else None
        }


def get_agent_stats(days: int = 7) -> dict:
    """Get statistics for all agents in the last N days"""
    with Session(engine) as session:
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get agents with tasks in the specified period
        stmt = select(UserTaskInfo.agent).where(
            UserTaskInfo.created_at >= since
        ).distinct()
        agents = session.exec(stmt).all()
        
        agent_stats = []
        total_tasks_all = 0
        total_completed_all = 0
        
        for agent in agents:
            if not agent:  # Skip None values
                continue
                
            # Get tasks for this agent in the period
            agent_stmt = select(UserTaskInfo).where(
                UserTaskInfo.agent == agent,
                UserTaskInfo.created_at >= since
            )
            agent_tasks = session.exec(agent_stmt).all()
            
            total_tasks = len(agent_tasks)
            completed_tasks = len([t for t in agent_tasks if t.status == "completed"])
            
            # Calculate average completion time
            completed_task_times = [
                (task.completed_at - task.created_at).total_seconds()
                for task in agent_tasks 
                if task.status == "completed" and task.completed_at and task.created_at
            ]
            avg_completion_time = sum(completed_task_times) / len(completed_task_times) if completed_task_times else 0
            
            agent_stats.append({
                "agent": agent,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "average_completion_time_seconds": avg_completion_time
            })
            
            total_tasks_all += total_tasks
            total_completed_all += completed_tasks
        
        return {
            "period_days": days,
            "total_agents": len(agent_stats),
            "agents": agent_stats,
            "summary": {
                "total_tasks_all_agents": total_tasks_all,
                "total_completed_all_agents": total_completed_all,
                "overall_completion_rate": (total_completed_all / total_tasks_all * 100) if total_tasks_all > 0 else 0
            }
        }


def create_agent(agent: str) -> dict:
    """Create a new agent without assigning any tasks"""
    with Session(engine) as session:
        # Check if agent already exists by looking for any tasks
        stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent).limit(1)
        existing_task = session.exec(stmt).first()
        
        if existing_task:
            return {
                "agent": agent,
                "status": "already_exists",
                "message": f"Agent '{agent}' already exists with existing tasks",
                "existing_tasks": True
            }
        
        # Create a placeholder task that will be immediately marked as a "registration" task
        placeholder_task = UserTaskInfo(
            agent=agent,
            task_id=-1,  # Use -1 to indicate this is a registration placeholder
            status="agent_created",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),  # Mark as completed immediately
            workbench_id=None
        )
        
        session.add(placeholder_task)
        session.commit()
        session.refresh(placeholder_task)
        
        return {
            "agent": agent,
            "status": "created",
            "message": f"Agent '{agent}' created successfully without tasks",
            "created_at": placeholder_task.created_at.isoformat(),
            "registration_id": placeholder_task.id
        }


def assign_role(agent: str, role: str, workbench_id: Optional[int] = None, workbench_name: Optional[str] = None) -> dict:
    """Assign a role to an agent, optionally for a specific workbench"""
    with Session(engine) as session:
        # Check if agent exists by looking for any tasks
        stmt = select(UserTaskInfo).where(UserTaskInfo.agent == agent).limit(1)
        existing_task = session.exec(stmt).first()
        
        if not existing_task:
            return {
                "agent": agent,
                "status": "error",
                "message": f"Agent '{agent}' not found. Create agent first.",
                "role_assigned": False
            }
        
        # Create a special role assignment task
        role_task = UserTaskInfo(
            agent=agent,
            task_id=-100 - (workbench_id or 0),  # Use negative numbers for role assignments
            status=f"role_{role.lower().replace(' ', '_')}",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),  # Mark as completed immediately
            workbench_id=workbench_id
        )
        
        session.add(role_task)
        session.commit()
        session.refresh(role_task)
        
        workbench_info = ""
        if workbench_name and workbench_id:
            workbench_info = f" for {workbench_name} (Workbench ID: {workbench_id})"
        elif workbench_id:
            workbench_info = f" for Workbench ID: {workbench_id}"
        
        return {
            "agent": agent,
            "role": role,
            "workbench_id": workbench_id,
            "workbench_name": workbench_name,
            "status": "role_assigned",
            "message": f"Agent '{agent}' assigned as {role}{workbench_info}",
            "assigned_at": role_task.created_at.isoformat(),
            "role_id": role_task.id
        }


def get_agent_roles(agent: Optional[str] = None) -> dict:
    """Get roles for a specific agent or all agents"""
    with Session(engine) as session:
        if agent:
            # Get roles for specific agent
            stmt = select(UserTaskInfo).where(
                UserTaskInfo.agent == agent,
                UserTaskInfo.status.like("role_%")
            ).order_by(UserTaskInfo.created_at.desc())
            role_tasks = session.exec(stmt).all()
            
            roles = []
            for task in role_tasks:
                role_name = task.status.replace("role_", "").replace("_", " ").title()
                roles.append({
                    "role": role_name,
                    "workbench_id": task.workbench_id,
                    "assigned_at": task.created_at.isoformat(),
                    "role_id": task.id
                })
            
            return {
                "agent": agent,
                "roles": roles,
                "total_roles": len(roles)
            }
        else:
            # Get all agents with roles
            stmt = select(UserTaskInfo).where(
                UserTaskInfo.status.like("role_%")
            ).order_by(UserTaskInfo.agent, UserTaskInfo.created_at.desc())
            role_tasks = session.exec(stmt).all()
            
            agents_roles = {}
            for task in role_tasks:
                agent_name = task.agent
                if agent_name not in agents_roles:
                    agents_roles[agent_name] = []
                
                role_name = task.status.replace("role_", "").replace("_", " ").title()
                agents_roles[agent_name].append({
                    "role": role_name,
                    "workbench_id": task.workbench_id,
                    "assigned_at": task.created_at.isoformat(),
                    "role_id": task.id
                })
            
            return {
                "all_agents_roles": agents_roles,
                "total_agents_with_roles": len(agents_roles)
            }
