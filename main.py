from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine

# Import routers
from routers import (
    tenant,
    tags,
    task_queue_mapping,
    user_task_info,
    history_task_info,
    performance
)

app = FastAPI(title="OPS Center MCP Server")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/health")
def health():
    return {"status": "OK"}

# Include routers
app.include_router(tenant.router)
app.include_router(tags.router)
app.include_router(task_queue_mapping.router)
app.include_router(user_task_info.router)
app.include_router(history_task_info.router)
app.include_router(performance.router)
