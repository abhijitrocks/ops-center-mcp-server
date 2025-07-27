from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


# Import routers
from routers import (
    tenant,
    tags,
    task_queue_mapping,
    user_task_info,
    history_task_info,
    performance,
    agents
)

app = FastAPI(title="OPS Center MCP Server")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/health")
def health():
    return {"status": "OK"}

@app.get("/ai-plugin.json", include_in_schema=False)
def plugin_manifest():
    return FileResponse("static/ai-plugin.json", media_type="application/json")


# Include routers
app.include_router(tenant.router)
app.include_router(tags.router)
app.include_router(task_queue_mapping.router)
app.include_router(user_task_info.router)
app.include_router(history_task_info.router)
app.include_router(performance.router)
app.include_router(agents.router)
