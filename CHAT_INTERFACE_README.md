# 🤖 MCP Chat Interface

A modern, shareable web interface for interacting with the MCP (Model Context Protocol) system through a beautiful chat-style interface.

## 🚀 Quick Start

### Option 1: Using the startup script
```bash
./start_chat_interface.sh
```

### Option 2: Manual start
```bash
python3 web_chat_interface.py
```

The interface will be available at: **http://localhost:8080**

## 🔗 Sharing with Others

1. **Local Network**: Share `http://YOUR_IP:8080` with colleagues on the same network
2. **Internet**: Use port forwarding or a reverse proxy to make it accessible over the internet
3. **Cloud**: Deploy to a cloud service and share the public URL

## 💬 Available Commands

### 🏢 **System Commands**
- `help` - Show all available commands
- `agents` - List all agents in the system
- `workbenches` - List all workbenches with descriptions

### 🎭 **Role Management**
- `roles <workbench_id>` - Show roles in a specific workbench
- `assign-role <agent> <workbench_id> <role>` - Assign a role to an agent
- `agent-roles <agent>` - Show all roles for a specific agent
- `coverage` - Show role coverage report across workbenches

### 📋 **Task Management** (requires MCP server)
- `tasks <agent>` - Get recent tasks for an agent
- `assign <agent> <task_id> [workbench_id]` - Assign task to agent
- `status <task_id> <agent> <status>` - Update task status
- `stats <agent>` - Get agent statistics

## 🎯 Example Commands

```
help
agents
workbenches
roles 1
assign-role ashish 1 Reviewer
agent-roles abhijit
coverage
```

## 🏗️ System Architecture

### Features
- **Real-time WebSocket communication**
- **Modern, responsive UI**
- **Role-based workbench management**
- **Demo mode when MCP server unavailable**
- **Auto-reconnection**
- **Command history**

### Components
- **FastAPI backend** with WebSocket support
- **SQLite database** for workbench and role data
- **HTML/CSS/JavaScript frontend** with modern styling
- **MCP Client integration** for task management
- **Workbench Role Manager** for role assignments

## 🔧 Technical Details

### Dependencies
- FastAPI
- Uvicorn (ASGI server)
- Jinja2 (templating)
- WebSockets
- Python 3.7+

### Ports
- **8080**: Web interface (configurable)
- **8000**: MCP server (if available)

### Database
- SQLite database: `ops_center.db`
- Tables: `workbench`, `workbench_roles`, `usertaskinfo`, etc.

## 🎨 User Interface

### Design Features
- **Modern gradient background**
- **Chat-style message bubbles**
- **Real-time connection status**
- **Command syntax highlighting**
- **Responsive design** for mobile/desktop
- **Visual indicators** for demo mode

### Color Scheme
- **Primary**: Blue gradient (#667eea to #764ba2)
- **Success**: Green (#48bb78)
- **Error**: Red (#f56565)
- **Info**: Gray (#e2e8f0)

## 📊 Workbench System

### Available Workbenches
1. **Dispute** - Handle customer disputes and resolution processes
2. **Transaction** - Process and manage financial transactions
3. **Account Holder** - Manage account holder information and services
4. **Loan** - Process loan applications and loan management

### Standard Roles (per workbench)
1. **Assessor** - Primary evaluator of tasks
2. **Reviewer** - Secondary review and validation
3. **Team Lead** - Leadership and coordination
4. **Viewer** - Read-only access and monitoring

## 🔒 Security Considerations

- The interface runs on localhost by default
- No authentication built-in (add if needed for production)
- Direct database access (secure your database)
- WebSocket connections are unencrypted (use WSS in production)

## 🛠️ Customization

### Changing the Port
Edit `web_chat_interface.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=YOUR_PORT)
```

### Adding Authentication
Implement FastAPI authentication middleware or use a reverse proxy with auth.

### Custom Styling
Modify the CSS in the `chat_html_template` variable in `web_chat_interface.py`.

## 🐛 Troubleshooting

### Interface won't start
- Check Python 3 is installed
- Install dependencies: `pip install fastapi uvicorn jinja2 websockets`
- Check port 8080 is available

### Commands not working
- **MCP commands**: Ensure MCP server is running on port 8000
- **Role commands**: Check `ops_center.db` exists and has workbench tables
- **Demo mode**: Some features show demo data when servers unavailable

### Connection issues
- Check firewall settings
- Verify network connectivity
- Try `curl http://localhost:8080/api/health`

## 📝 Development

### Adding New Commands
1. Add command to `process_command` method
2. Add help text to help command
3. Implement frontend formatting in `formatResult`

### Database Schema
The interface uses these main tables:
- `workbench` - Workbench definitions
- `workbench_roles` - Role assignments
- `usertaskinfo` - Task information
- `historytaskinfo` - Task history

## 🤝 Contributing

Feel free to enhance the interface by:
- Adding new commands
- Improving the UI/UX
- Adding authentication
- Implementing real-time notifications
- Adding file upload/download capabilities

## 📜 License

This chat interface is part of the MCP system and follows the same licensing terms.

---

**Happy chatting! 🎉**

For support or questions, refer to the main MCP system documentation.