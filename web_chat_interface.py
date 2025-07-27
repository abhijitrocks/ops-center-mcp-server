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

app = FastAPI(title="MCP Chat Interface", description="Web interface for MCP Client")

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
                config = MCPClientConfig(server_url="http://localhost:8000")
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
                return {"error": f"Unknown command: {action}. Type 'help' for available commands."}
        
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
                "workbench_manager_available": WORKBENCH_MANAGER_AVAILABLE
            }
        }
        await manager.send_personal_message(json.dumps(welcome_msg), websocket)
        
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

# Create the HTML template
chat_html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Chat Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 900px;
            height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: #4a5568;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 15px 15px 0 0;
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
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 MCP Chat Interface</h1>
            <p>Interactive command interface for MCP system | Type 'help' to get started</p>
        </div>
        
        <div class="chat-messages" id="messages">
            <!-- Messages will appear here -->
        </div>
        
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type a command (e.g., 'help', 'agents', 'workbenches', 'roles 1')..." maxlength="500">
            <button onclick="sendMessage()">Send</button>
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
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${userId}`;
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                updateConnectionStatus(true);
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                displayMessage(data);
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
                
                let statusIndicator = '';
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
                roles.forEach(role => {
                    html += `<div class="role-assignment">
                        ${role.workbench_name}: <strong>${role.role}</strong>
                    </div>`;
                });
                html += '</div>';
                return html;
            }
            
            if (result.type === 'coverage_report') {
                const report = result.data;
                let html = '<strong>📊 Role Coverage Report:</strong><div class="workbench-list">';
                report.workbenches.forEach(wb => {
                    html += `<div class="workbench-item">
                        <strong>${wb.workbench_name}:</strong> ${wb.coverage_percentage.toFixed(0)}% coverage (${wb.gaps} gaps)
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
    print("📱 Chat interface will be available at: http://localhost:8080")
    print("🔗 Share this URL with others to give them access to the MCP system")
    print("💡 Available commands: help, agents, workbenches, roles, assign-role, agent-roles, coverage")
    print(f"🔧 MCP Client Available: {MCP_AVAILABLE}")
    print(f"🔧 Workbench Manager Available: {WORKBENCH_MANAGER_AVAILABLE}")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)