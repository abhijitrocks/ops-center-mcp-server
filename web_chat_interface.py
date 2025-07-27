#!/usr/bin/env python3
"""
Web Chat Interface for MCP Client
A shareable web interface for interacting with the MCP system
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any
import uvicorn
from pathlib import Path
import sqlite3

# Import our MCP client and workbench manager
try:
    from mcp_client import MCPClient, MCPClientConfig
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP Client not available. Running in demo mode.")

try:
    from workbench_role_manager import WorkbenchRoleManager
    WORKBENCH_MANAGER_AVAILABLE = True
except ImportError:
    WORKBENCH_MANAGER_AVAILABLE = False
    print("Warning: Workbench Role Manager not available.")

# Environment variables
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

app = FastAPI(
    title="MCP Chat Interface", 
    description="Web interface for MCP Client",
    version="1.0.0"
)

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.mcp_client = None
        self.role_manager = None
        
        if MCP_AVAILABLE:
            try:
                config = MCPClientConfig(server_url=MCP_SERVER_URL)
                self.mcp_client = MCPClient(config)
            except Exception as e:
                print(f"Could not initialize MCP client: {e}")
        
        if WORKBENCH_MANAGER_AVAILABLE:
            try:
                self.role_manager = WorkbenchRoleManager()
            except Exception as e:
                print(f"Could not initialize workbench role manager: {e}")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def get_demo_data(self, action: str) -> Dict[str, Any]:
        """Provide demo data when MCP client is not available"""
        demo_data = {
            "agents": {
                "type": "agents",
                "data": {
                    "agents": ["Chitra", "abhijit", "ashish", "ramesh", "Aleem", "bulk_agent", "test_agent", "workflow_agent"],
                    "total_agents": 8
                }
            },
            "workbenches": {
                "type": "workbenches",
                "data": [
                    {"id": 1, "name": "Dispute", "description": "Handle customer disputes"},
                    {"id": 2, "name": "Transaction", "description": "Process transactions"},
                    {"id": 3, "name": "Account Holder", "description": "Manage accounts"},
                    {"id": 4, "name": "Loan", "description": "Process loans"}
                ]
            }
        }
        return demo_data.get(action, {"error": "Demo data not available"})

    def get_suggested_prompts(self) -> List[Dict[str, str]]:
        """Get comprehensive suggested prompts for all features"""
        prompts = [
            # Getting Started
            {"category": "🚀 Getting Started", "prompt": "help", "description": "Show all available commands"},
            {"category": "🚀 Getting Started", "prompt": "agents", "description": "List all agents in the system"},
            {"category": "🚀 Getting Started", "prompt": "workbenches", "description": "Show all workbenches with descriptions"},
            
            # Agent Management
            {"category": "👥 Agent Management", "prompt": "agent-roles abhijit", "description": "Show all roles for abhijit"},
            {"category": "👥 Agent Management", "prompt": "agent-roles Chitra", "description": "Show all roles for Chitra"},
            {"category": "👥 Agent Management", "prompt": "agent-roles ashish", "description": "Show all roles for ashish"},
            
            # Workbench Operations
            {"category": "🏢 Workbench Operations", "prompt": "roles 1", "description": "View roles in Dispute workbench"},
            {"category": "🏢 Workbench Operations", "prompt": "roles 2", "description": "View roles in Transaction workbench"},
            {"category": "🏢 Workbench Operations", "prompt": "roles 3", "description": "View roles in Account Holder workbench"},
            {"category": "🏢 Workbench Operations", "prompt": "roles 4", "description": "View roles in Loan workbench"},
            
            # Role Management
            {"category": "🎭 Role Management", "prompt": "assign-role bulk_agent 2 Viewer", "description": "Assign bulk_agent as Viewer in Transaction workbench"},
            {"category": "🎭 Role Management", "prompt": "assign-role ramesh 3 Assessor", "description": "Assign ramesh as Assessor in Account Holder workbench"},
            {"category": "🎭 Role Management", "prompt": "assign-role Aleem 1 Reviewer", "description": "Assign Aleem as Reviewer in Dispute workbench"},
            {"category": "🎭 Role Management", "prompt": "assign-role test_agent 4 Team Lead", "description": "Assign test_agent as Team Lead in Loan workbench"},
            
            # Analytics & Reports
            {"category": "📊 Analytics & Reports", "prompt": "coverage", "description": "Show role coverage across all workbenches"},
            
            # Task Management (if MCP available)
            {"category": "📋 Task Management", "prompt": "tasks abhijit", "description": "Get recent tasks for abhijit"},
            {"category": "📋 Task Management", "prompt": "tasks Chitra", "description": "Get recent tasks for Chitra"},
            {"category": "📋 Task Management", "prompt": "assign abhijit 5001 1", "description": "Assign task 5001 to abhijit in Dispute workbench"},
            {"category": "📋 Task Management", "prompt": "status 5001 abhijit completed", "description": "Mark task 5001 as completed for abhijit"},
            {"category": "📋 Task Management", "prompt": "stats abhijit", "description": "Get performance statistics for abhijit"},
            {"category": "📋 Task Management", "prompt": "stats Chitra", "description": "Get performance statistics for Chitra"},
            
            # Advanced Operations
            {"category": "⚡ Advanced Operations", "prompt": "assign-role workflow_agent 1 Assessor", "description": "Assign workflow_agent multiple roles"},
            {"category": "⚡ Advanced Operations", "prompt": "assign-role bulk_agent 3 Team Lead", "description": "Assign bulk_agent as team lead"},
            {"category": "⚡ Advanced Operations", "prompt": "assign-role test_agent 2 Reviewer", "description": "Cross-workbench role assignment"},
            
            # Specific Workbench Examples
            {"category": "🔍 Dispute Workbench", "prompt": "roles 1", "description": "Check current Dispute team"},
            {"category": "🔍 Dispute Workbench", "prompt": "assign-role ramesh 1 Viewer", "description": "Add ramesh as Dispute viewer"},
            
            {"category": "💳 Transaction Workbench", "prompt": "roles 2", "description": "Check Transaction team setup"},
            {"category": "💳 Transaction Workbench", "prompt": "assign-role ashish 2 Assessor", "description": "Add ashish to Transaction team"},
            
            {"category": "👤 Account Holder Workbench", "prompt": "roles 3", "description": "View Account Holder team"},
            {"category": "👤 Account Holder Workbench", "prompt": "assign-role Aleem 3 Reviewer", "description": "Add Aleem as Account reviewer"},
            
            {"category": "🏦 Loan Workbench", "prompt": "roles 4", "description": "Check Loan processing team"},
            {"category": "🏦 Loan Workbench", "prompt": "assign-role Chitra 4 Team Lead", "description": "Make Chitra loan team lead"},
            
            # System Insights
            {"category": "🔍 System Insights", "prompt": "coverage", "description": "Identify workbenches needing attention"},
            {"category": "🔍 System Insights", "prompt": "agent-roles bulk_agent", "description": "See bulk_agent's current responsibilities"},
            {"category": "🔍 System Insights", "prompt": "agent-roles workflow_agent", "description": "Check workflow_agent assignments"},
        ]
        
        # Filter out MCP-only commands if not available
        if not MCP_AVAILABLE:
            prompts = [p for p in prompts if p["category"] != "📋 Task Management"]
        
        return prompts

    async def process_command(self, command: str, user: str = "Anonymous") -> Dict[str, Any]:
        """Process MCP commands and return results"""
        try:
            # Parse command
            parts = command.strip().split()
            if not parts:
                return {"error": "Empty command"}
            
            action = parts[0].lower()
            
            # Handle different commands
            if action == "help":
                return {
                    "type": "help",
                    "commands": [
                        "help - Show available commands",
                        "agents - List all agents",
                        "workbenches - List all workbenches",
                        "tasks <agent> - Get tasks for agent",
                        "assign <agent> <task_id> [workbench_id] - Assign task to agent",
                        "status <task_id> <agent> <status> - Update task status",
                        "roles <workbench_id> - Show workbench roles",
                        "assign-role <agent> <workbench_id> <role> - Assign workbench role",
                        "agent-roles <agent> - Show agent's roles",
                        "coverage - Show role coverage report",
                        "stats <agent> - Get agent statistics"
                    ]
                }
            
            elif action == "prompts" or action == "suggestions":
                prompts = self.get_suggested_prompts()
                return {"type": "suggested_prompts", "data": prompts}
            
            elif action == "agents":
                if self.mcp_client:
                    result = self.mcp_client.list_agents()
                    return {"type": "agents", "data": result}
                else:
                    return self.get_demo_data("agents")
            
            elif action == "workbenches":
                if self.role_manager:
                    try:
                        conn = sqlite3.connect("ops_center.db")
                        cursor = conn.cursor()
                        cursor.execute('SELECT id, name, description FROM workbench ORDER BY id')
                        workbenches = cursor.fetchall()
                        conn.close()
                        
                        wb_list = [{"id": wb[0], "name": wb[1], "description": wb[2]} for wb in workbenches]
                        return {"type": "workbenches", "data": wb_list}
                    except Exception as e:
                        return {"error": f"Could not fetch workbenches: {e}"}
                else:
                    return self.get_demo_data("workbenches")
            
            elif action == "roles" and len(parts) > 1:
                if self.role_manager:
                    try:
                        workbench_id = int(parts[1])
                        assignments = self.role_manager.get_workbench_role_assignments(workbench_id)
                        return {"type": "workbench_roles", "data": assignments}
                    except Exception as e:
                        return {"error": f"Could not get workbench roles: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "assign-role" and len(parts) > 3:
                if self.role_manager:
                    try:
                        agent = parts[1]
                        workbench_id = int(parts[2])
                        role = parts[3]
                        success = self.role_manager.assign_workbench_role(agent, workbench_id, role, user)
                        if success:
                            return {"type": "role_assignment", "message": f"✅ Assigned {role} to {agent} in workbench {workbench_id}"}
                        else:
                            return {"error": "Role assignment failed (may already exist)"}
                    except Exception as e:
                        return {"error": f"Could not assign role: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "agent-roles" and len(parts) > 1:
                if self.role_manager:
                    try:
                        agent = parts[1]
                        roles = self.role_manager.get_agent_workbench_roles(agent)
                        return {"type": "agent_roles", "agent": agent, "data": roles}
                    except Exception as e:
                        return {"error": f"Could not get agent roles: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "coverage":
                if self.role_manager:
                    try:
                        report = self.role_manager.get_workbench_coverage_report()
                        return {"type": "coverage_report", "data": report}
                    except Exception as e:
                        return {"error": f"Could not get coverage report: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "tasks" and len(parts) > 1:
                if self.mcp_client:
                    agent = parts[1]
                    result = self.mcp_client.list_recent_tasks(agent, limit=10)
                    return {"type": "tasks", "agent": agent, "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "assign" and len(parts) > 2:
                if self.mcp_client:
                    agent = parts[1]
                    task_id = int(parts[2])
                    workbench_id = int(parts[3]) if len(parts) > 3 else None
                    result = self.mcp_client.assign_task(agent, task_id, workbench_id)
                    return {"type": "assignment", "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "status" and len(parts) > 3:
                if self.mcp_client:
                    task_id = int(parts[1])
                    agent = parts[2]
                    status = parts[3]
                    result = self.mcp_client.update_task_status(task_id, agent, status)
                    return {"type": "status_update", "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "stats" and len(parts) > 1:
                if self.mcp_client:
                    agent = parts[1]
                    task_count = self.mcp_client.get_agent_task_count(agent, days=7)
                    avg_time = self.mcp_client.average_completion_time(agent)
                    return {
                        "type": "stats", 
                        "agent": agent,
                        "task_count": task_count,
                        "avg_time": avg_time
                    }
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            else:
                return {"error": f"Unknown command: {action}. Type 'help' for available commands or 'prompts' for suggestions."}
        
        except Exception as e:
            return {"error": f"Error processing command: {str(e)}"}

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket)
    try:
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": f"Welcome {user_id}! Connected to MCP Chat Interface.",
            "timestamp": datetime.now().isoformat(),
            "status": {
                "mcp_available": MCP_AVAILABLE,
                "workbench_manager_available": WORKBENCH_MANAGER_AVAILABLE,
                "deployment": "cloud" if PORT != 8080 or HOST != "0.0.0.0" else "local"
            }
        }
        await manager.send_personal_message(json.dumps(welcome_msg), websocket)
        
        # Send suggested prompts
        prompts_msg = {
            "type": "suggested_prompts",
            "data": manager.get_suggested_prompts(),
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(json.dumps(prompts_msg), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            command = message_data.get("message", "")
            
            # Process the command
            result = await manager.process_command(command, user_id)
            
            # Send response
            response = {
                "type": "response",
                "user": user_id,
                "command": command,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mcp_available": MCP_AVAILABLE,
        "workbench_manager_available": WORKBENCH_MANAGER_AVAILABLE,
        "deployment": "cloud" if PORT != 8080 or HOST != "0.0.0.0" else "local",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents")
async def get_agents():
    """REST endpoint to get agents"""
    if not manager.mcp_client:
        return manager.get_demo_data("agents")
    
    try:
        result = manager.mcp_client.list_agents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/prompts")
async def get_suggested_prompts():
    """REST endpoint to get suggested prompts"""
    return {"prompts": manager.get_suggested_prompts()}

# Create the HTML template with enhanced UI for suggested prompts
chat_html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Chat Interface</title>
    <meta name="description" content="Interactive web interface for MCP system">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 1200px;
            height: 90vh;
            min-height: 600px;
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background: #f8fafc;
            border-right: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .sidebar-header {
            background: #4a5568;
            color: white;
            padding: 15px;
            text-align: center;
        }
        
        .sidebar-header h3 {
            font-size: 16px;
            margin-bottom: 5px;
        }
        
        .sidebar-header p {
            font-size: 12px;
            opacity: 0.8;
        }
        
        .prompts-container {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }
        
        .prompt-category {
            margin-bottom: 20px;
        }
        
        .category-title {
            font-size: 14px;
            font-weight: bold;
            color: #4a5568;
            margin-bottom: 8px;
            padding: 5px 0;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .prompt-item {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
            margin: 5px 0;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13px;
        }
        
        .prompt-item:hover {
            background: #edf2f7;
            border-color: #4299e1;
            transform: translateY(-1px);
        }
        
        .prompt-command {
            font-family: monospace;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 3px;
        }
        
        .prompt-description {
            color: #718096;
            font-size: 11px;
        }
        
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: #4a5568;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            opacity: 0.8;
            font-size: 14px;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f7fafc;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
        }
        
        .message.user {
            background: #4299e1;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .message.system {
            background: #48bb78;
            color: white;
            text-align: center;
            max-width: 100%;
            font-size: 14px;
        }
        
        .message.response {
            background: #e2e8f0;
            color: #2d3748;
        }
        
        .message.error {
            background: #f56565;
            color: white;
        }
        
        .message-time {
            font-size: 12px;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 25px;
            outline: none;
            font-size: 16px;
        }
        
        .chat-input input:focus {
            border-color: #4299e1;
        }
        
        .chat-input button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .chat-input button:hover {
            background: #3182ce;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-size: 14px;
            z-index: 1000;
        }
        
        .connected {
            background: #48bb78;
        }
        
        .disconnected {
            background: #f56565;
        }
        
        .command-result {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 14px;
        }
        
        .help-commands {
            list-style: none;
            padding: 0;
        }
        
        .help-commands li {
            background: #edf2f7;
            margin: 5px 0;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
        }
        
        .workbench-list {
            margin: 10px 0;
        }
        
        .workbench-item {
            background: #f0f4f8;
            border: 1px solid #cbd5e0;
            border-radius: 6px;
            padding: 10px;
            margin: 5px 0;
        }
        
        .role-assignment {
            background: #e6fffa;
            border: 1px solid #81e6d9;
            border-radius: 6px;
            padding: 8px;
            margin: 5px 0;
        }
        
        .demo-indicator {
            background: #fed7d7;
            color: #c53030;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .cloud-indicator {
            background: #d6f5d6;
            color: #2d7a2d;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .toggle-sidebar {
            display: none;
            background: #4a5568;
            color: white;
            border: none;
            padding: 10px;
            cursor: pointer;
            position: fixed;
            top: 20px;
            left: 20px;
            border-radius: 5px;
            z-index: 1001;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 5px;
            }
            
            .chat-container {
                height: 95vh;
                border-radius: 10px;
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                height: 250px;
                border-right: none;
                border-bottom: 1px solid #e2e8f0;
                display: none;
            }
            
            .sidebar.mobile-open {
                display: flex;
            }
            
            .main-chat {
                flex: 1;
            }
            
            .toggle-sidebar {
                display: block;
            }
            
            .chat-header {
                padding: 15px;
            }
            
            .chat-header h1 {
                font-size: 20px;
            }
            
            .chat-messages {
                padding: 15px;
            }
            
            .chat-input {
                padding: 15px;
            }
            
            .connection-status {
                top: 10px;
                right: 10px;
                font-size: 12px;
                padding: 8px 12px;
            }
        }
    </style>
</head>
<body>
    <button class="toggle-sidebar" onclick="toggleSidebar()">💡 Prompts</button>
    
    <div class="chat-container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h3>💡 Suggested Prompts</h3>
                <p>Click any prompt to try it</p>
            </div>
            <div class="prompts-container" id="promptsContainer">
                <!-- Prompts will be loaded here -->
            </div>
        </div>
        
        <div class="main-chat">
            <div class="chat-header">
                <h1>🤖 MCP Chat Interface</h1>
                <p>Interactive command interface for MCP system | Click prompts or type commands</p>
            </div>
            
            <div class="chat-messages" id="messages">
                <!-- Messages will appear here -->
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Type a command or click a suggested prompt..." maxlength="500">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <div class="connection-status disconnected" id="connectionStatus">
        Connecting...
    </div>
    
    <script>
        let socket;
        let userId = 'User_' + Math.random().toString(36).substr(2, 9);
        let mcpAvailable = false;
        let workbenchManagerAvailable = false;
        let isCloudDeployment = false;
        let suggestedPrompts = [];
        
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('mobile-open');
        }
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${userId}`;
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                updateConnectionStatus(true);
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'suggested_prompts') {
                    suggestedPrompts = data.data;
                    displaySuggestedPrompts(data.data);
                } else {
                    displayMessage(data);
                }
            };
            
            socket.onclose = function(event) {
                updateConnectionStatus(false);
                setTimeout(connect, 3000); // Reconnect after 3 seconds
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false);
            };
        }
        
        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connectionStatus');
            if (connected) {
                statusEl.textContent = '🟢 Connected';
                statusEl.className = 'connection-status connected';
            } else {
                statusEl.textContent = '🔴 Disconnected';
                statusEl.className = 'connection-status disconnected';
            }
        }
        
        function displaySuggestedPrompts(prompts) {
            const container = document.getElementById('promptsContainer');
            container.innerHTML = '';
            
            // Group prompts by category
            const categories = {};
            prompts.forEach(prompt => {
                if (!categories[prompt.category]) {
                    categories[prompt.category] = [];
                }
                categories[prompt.category].push(prompt);
            });
            
            // Display each category
            Object.entries(categories).forEach(([category, categoryPrompts]) => {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'prompt-category';
                
                const titleDiv = document.createElement('div');
                titleDiv.className = 'category-title';
                titleDiv.textContent = category;
                categoryDiv.appendChild(titleDiv);
                
                categoryPrompts.forEach(prompt => {
                    const promptDiv = document.createElement('div');
                    promptDiv.className = 'prompt-item';
                    promptDiv.onclick = () => selectPrompt(prompt.prompt);
                    
                    promptDiv.innerHTML = `
                        <div class="prompt-command">${prompt.prompt}</div>
                        <div class="prompt-description">${prompt.description}</div>
                    `;
                    
                    categoryDiv.appendChild(promptDiv);
                });
                
                container.appendChild(categoryDiv);
            });
        }
        
        function selectPrompt(prompt) {
            const input = document.getElementById('messageInput');
            input.value = prompt;
            input.focus();
            
            // Auto-send on mobile
            if (window.innerWidth <= 768) {
                sendMessage();
                toggleSidebar(); // Close sidebar on mobile
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (message === '' || !socket || socket.readyState !== WebSocket.OPEN) {
                return;
            }
            
            // Display user message
            displayMessage({
                type: 'user',
                message: message,
                timestamp: new Date().toISOString()
            });
            
            // Send to server
            socket.send(JSON.stringify({
                message: message,
                user: userId
            }));
            
            input.value = '';
        }
        
        function displayMessage(data) {
            const messagesEl = document.getElementById('messages');
            const messageEl = document.createElement('div');
            
            let className = 'message ';
            let content = '';
            
            if (data.type === 'user') {
                className += 'user';
                content = `
                    <div>${data.message}</div>
                    <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
                `;
            } else if (data.type === 'system') {
                className += 'system';
                mcpAvailable = data.status?.mcp_available || false;
                workbenchManagerAvailable = data.status?.workbench_manager_available || false;
                isCloudDeployment = data.status?.deployment === 'cloud';
                
                let statusIndicator = '';
                if (isCloudDeployment) statusIndicator += '<span class="cloud-indicator">🌐 Cloud Deployed</span>';
                if (!mcpAvailable) statusIndicator += '<span class="demo-indicator">MCP Demo Mode</span>';
                if (!workbenchManagerAvailable) statusIndicator += '<span class="demo-indicator">Role Manager Unavailable</span>';
                
                content = `
                    <div>${data.message} ${statusIndicator}</div>
                    <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
                `;
            } else if (data.type === 'response') {
                className += 'response';
                content = `
                    <div><strong>Command:</strong> ${data.command}</div>
                    <div class="command-result">${formatResult(data.result)}</div>
                    <div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>
                `;
            }
            
            messageEl.className = className;
            messageEl.innerHTML = content;
            messagesEl.appendChild(messageEl);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
        
        function formatResult(result) {
            if (result.error) {
                let errorMsg = `<span style="color: #f56565;">❌ Error: ${result.error}</span>`;
                if (result.demo) {
                    errorMsg += '<br><span class="demo-indicator">Running in demo mode</span>';
                }
                return errorMsg;
            }
            
            if (result.type === 'help') {
                let html = '<strong>📚 Available Commands:</strong><ul class="help-commands">';
                result.commands.forEach(cmd => {
                    html += `<li>${cmd}</li>`;
                });
                html += '</ul>';
                html += '<p style="margin-top: 10px;"><em>💡 Tip: Check the sidebar for suggested prompts or type "prompts" to see all suggestions!</em></p>';
                return html;
            }
            
            if (result.type === 'suggested_prompts') {
                let html = '<strong>💡 All Available Prompts:</strong><div class="workbench-list">';
                const categories = {};
                result.data.forEach(prompt => {
                    if (!categories[prompt.category]) {
                        categories[prompt.category] = [];
                    }
                    categories[prompt.category].push(prompt);
                });
                
                Object.entries(categories).forEach(([category, prompts]) => {
                    html += `<div class="workbench-item"><strong>${category}</strong>`;
                    prompts.forEach(prompt => {
                        html += `<div class="role-assignment" style="cursor: pointer;" onclick="selectPrompt('${prompt.prompt}')">
                            <strong>${prompt.prompt}</strong><br>
                            <small>${prompt.description}</small>
                        </div>`;
                    });
                    html += '</div>';
                });
                html += '</div>';
                return html;
            }
            
            if (result.type === 'agents') {
                const agents = result.data.agents || [];
                return `<strong>👥 Agents (${agents.length}):</strong><br>${agents.join(', ')}`;
            }
            
            if (result.type === 'workbenches') {
                let html = '<strong>🏢 Workbenches:</strong><div class="workbench-list">';
                result.data.forEach(wb => {
                    html += `<div class="workbench-item">
                        <strong>${wb.id}. ${wb.name}</strong><br>
                        <small>${wb.description}</small>
                    </div>`;
                });
                html += '</div>';
                return html;
            }
            
            if (result.type === 'workbench_roles') {
                const wb = result.data;
                let html = `<strong>🎭 Roles in ${wb.workbench_name}:</strong><div class="workbench-list">`;
                Object.entries(wb.roles).forEach(([role, agents]) => {
                    html += `<div class="role-assignment">
                        <strong>${role}:</strong> ${agents.length > 0 ? agents.map(a => a.agent).join(', ') : '(vacant)'}
                    </div>`;
                });
                html += '</div>';
                return html;
            }
            
            if (result.type === 'agent_roles') {
                const roles = result.data;
                let html = `<strong>🎭 Roles for ${result.agent}:</strong><div class="workbench-list">`;
                if (roles.length === 0) {
                    html += '<div class="role-assignment">No roles assigned</div>';
                } else {
                    roles.forEach(role => {
                        html += `<div class="role-assignment">
                            ${role.workbench_name}: <strong>${role.role}</strong>
                        </div>`;
                    });
                }
                html += '</div>';
                return html;
            }
            
            if (result.type === 'coverage_report') {
                const report = result.data;
                let html = '<strong>📊 Role Coverage Report:</strong><div class="workbench-list">';
                report.workbenches.forEach(wb => {
                    const statusColor = wb.gaps === 0 ? '#48bb78' : wb.gaps <= 2 ? '#ed8936' : '#f56565';
                    html += `<div class="workbench-item">
                        <strong style="color: ${statusColor};">${wb.workbench_name}:</strong> ${wb.coverage_percentage.toFixed(0)}% coverage (${wb.gaps} gaps)
                    </div>`;
                });
                html += '</div>';
                return html;
            }
            
            if (result.type === 'role_assignment') {
                return `<div class="role-assignment">${result.message}</div>`;
            }
            
            if (result.type === 'tasks') {
                const tasks = result.data || [];
                return `<strong>📋 Recent tasks for ${result.agent} (${tasks.length}):</strong><br><pre>${JSON.stringify(tasks, null, 2)}</pre>`;
            }
            
            if (result.type === 'stats') {
                return `<strong>📊 Stats for ${result.agent}:</strong><br>
                       Task Count: ${JSON.stringify(result.task_count)}<br>
                       Avg Time: ${JSON.stringify(result.avg_time)}`;
            }
            
            return `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        // Event listeners
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Connect on page load
        connect();
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    # Create the HTML template file
    with open("templates/chat.html", "w") as f:
        f.write(chat_html_template)
    
    print("🚀 Starting MCP Chat Interface...")
    print(f"📱 Chat interface will be available at: http://{HOST}:{PORT}")
    print("🔗 Share this URL with others to give them access to the MCP system")
    print("💡 Available commands: help, agents, workbenches, roles, assign-role, agent-roles, coverage")
    print(f"🔧 MCP Client Available: {MCP_AVAILABLE}")
    print(f"🔧 Workbench Manager Available: {WORKBENCH_MANAGER_AVAILABLE}")
    print(f"🌐 Deployment: {'Cloud' if PORT != 8080 or HOST != '0.0.0.0' else 'Local'}")
    
    uvicorn.run(app, host=HOST, port=PORT)