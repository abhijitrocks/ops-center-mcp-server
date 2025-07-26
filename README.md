# OPS Center MCP Server

A FastAPI-based CRUD server to manage tenants, tags, task mappings, and agent performance.

## Quick Start

1. **Clone the repo**:
   ```bash
   git clone https://github.com/YOUR_USER/ops-center-mcp-server.git
   cd ops-center-mcp-server

   ## JSON‑RPC 2.0 Interface

Endpoint: `POST /rpc`

Supported methods:
- `get_agent_task_count(agent: str, days: int)`
- `list_recent_tasks(agent: str, limit: int)`
- `average_completion_time(agent: str)`
- `list_tags(tenant_id: int)`
- `assign_task(agent: str, task_id: int, workbench_id: int)`
- `update_task_status(task_id: int, agent: str, status: str)`

Example payload:
```json
{
  "jsonrpc": "2.0",
  "method": "get_agent_task_count",
  "params": {"agent":"Agent A","days":3},
  "id": 1
}


---

## 4. Commit & push

```bash
git add rpc_server.py requirements.txt README.md
git commit -m "Add JSON-RPC 2.0 interface with full set of methods"
git push origin main

