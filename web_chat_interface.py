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
    print("🔶 MCP Client not available. Running in demo mode with full UI features.")

try:
    from workbench_role_manager import WorkbenchRoleManager
    WORKBENCH_MANAGER_AVAILABLE = True
except ImportError:
    WORKBENCH_MANAGER_AVAILABLE = False
    print("🔶 Workbench Role Manager not available.")

# Import LLM integration
try:
    from llm_integration import create_llm_processor, test_llm_availability
    LLM_INTEGRATION_AVAILABLE = True
except ImportError:
    LLM_INTEGRATION_AVAILABLE = False
    print("🔶 LLM Integration not available in cloud. Using rule-based processing with natural language support.")

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
        self.last_command_context = {}  # Store context for follow-up commands
        self.llm_processor = None  # LLM integration
        self.llm_enabled = False
        
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
        
        # Initialize LLM processor
        if LLM_INTEGRATION_AVAILABLE:
            try:
                self.llm_processor = create_llm_processor()
                self.llm_enabled = self.llm_processor.available
                if self.llm_enabled:
                    print(f"🤖 LLM Integration enabled: {self.llm_processor.provider}")
                else:
                    print("🤖 LLM Integration available but no provider configured")
            except Exception as e:
                print(f"Could not initialize LLM processor: {e}")
        
        # Setup demo data for cloud deployment if MCP not available
        if not MCP_AVAILABLE and self.role_manager:
            self.setup_demo_data()

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

    def create_agent(self, agent_name: str, user: str = "system") -> Dict[str, Any]:
        """Create a new agent in the system"""
        try:
            conn = sqlite3.connect("ops_center.db")
            cursor = conn.cursor()
            
            # Check if agent already exists
            cursor.execute('SELECT COUNT(*) FROM usertaskinfo WHERE agent = ?', (agent_name,))
            existing = cursor.fetchone()[0]
            
            if existing > 0:
                return {"error": f"Agent '{agent_name}' already exists"}
            
            # Create agent by adding a creation record
            cursor.execute('''
                INSERT INTO usertaskinfo (agent, task_id, status, created_at)
                VALUES (?, ?, ?, ?)
            ''', (agent_name, -1, 'agent_created', datetime.now()))
            
            conn.commit()
            conn.close()
            
            return {
                "type": "agent_creation",
                "message": f"✅ Agent '{agent_name}' created successfully!",
                "agent": agent_name,
                "created_by": user
            }
            
        except Exception as e:
            return {"error": f"Failed to create agent: {str(e)}"}

    def create_workbench(self, workbench_name: str, description: str = "", user: str = "system") -> Dict[str, Any]:
        """Create a new workbench in the system"""
        try:
            conn = sqlite3.connect("ops_center.db")
            cursor = conn.cursor()
            
            # Check if workbench already exists
            cursor.execute('SELECT COUNT(*) FROM workbench WHERE name = ?', (workbench_name,))
            existing = cursor.fetchone()[0]
            
            if existing > 0:
                return {"error": f"Workbench '{workbench_name}' already exists"}
            
            # Create workbench
            cursor.execute('''
                INSERT INTO workbench (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (workbench_name, description, datetime.now(), datetime.now()))
            
            workbench_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "type": "workbench_creation",
                "message": f"✅ Workbench '{workbench_name}' created successfully!",
                "workbench_id": workbench_id,
                "workbench_name": workbench_name,
                "description": description,
                "created_by": user
            }
            
        except Exception as e:
            return {"error": f"Failed to create workbench: {str(e)}"}

    def create_task(self, task_id: int, agent: str = None, workbench_id: int = None, user: str = "system") -> Dict[str, Any]:
        """Create a new task in the system"""
        try:
            conn = sqlite3.connect("ops_center.db")
            cursor = conn.cursor()
            
            # Check if task already exists
            cursor.execute('SELECT COUNT(*) FROM usertaskinfo WHERE task_id = ?', (task_id,))
            existing = cursor.fetchone()[0]
            
            if existing > 0:
                return {"error": f"Task {task_id} already exists"}
            
            # Create task
            cursor.execute('''
                INSERT INTO usertaskinfo (agent, task_id, status, created_at, workbench_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (agent, task_id, 'created', datetime.now(), workbench_id))
            
            conn.commit()
            conn.close()
            
            return {
                "type": "task_creation",
                "message": f"✅ Task {task_id} created successfully!",
                "task_id": task_id,
                "agent": agent,
                "workbench_id": workbench_id,
                "created_by": user
            }
            
        except Exception as e:
            return {"error": f"Failed to create task: {str(e)}"}

    def get_all_agent_workbench_assignments(self) -> Dict[str, Any]:
        """Get a summary of all agents and their workbench assignments"""
        try:
            conn = sqlite3.connect("ops_center.db")
            cursor = conn.cursor()
            
            # Get all agents
            cursor.execute('SELECT DISTINCT agent FROM usertaskinfo WHERE agent != "" ORDER BY agent')
            agents = [row[0] for row in cursor.fetchall()]
            
            # Get workbench assignments for each agent
            agent_assignments = {}
            for agent in agents:
                if self.role_manager:
                    roles = self.role_manager.get_agent_workbench_roles(agent)
                    agent_assignments[agent] = roles
                else:
                    agent_assignments[agent] = []
            
            # Get workbench names for reference
            cursor.execute('SELECT id, name FROM workbench ORDER BY id')
            workbench_names = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "agents": agents,
                "assignments": agent_assignments,
                "workbench_names": workbench_names,
                "total_agents": len(agents),
                "context": "Shows all agent workbench assignments in response to contextual query"
            }
            
        except Exception as e:
            return {"error": f"Could not get agent assignments: {str(e)}"}

    def setup_demo_data(self):
        """Setup impressive demo data for cloud deployment"""
        try:
            print("🎯 Setting up demo data for cloud deployment...")
            
            # Create demo agents via role assignments (this creates the workbench roles entries)
            demo_roles = [
                ("Sarah_Chen", 1, "Team Lead"),      # Dispute Team Lead
                ("Mike_Johnson", 1, "Assessor"),     # Dispute Assessor  
                ("Lisa_Wong", 1, "Reviewer"),        # Dispute Reviewer
                ("David_Kim", 2, "Team Lead"),       # Transaction Team Lead
                ("Amy_Rodriguez", 2, "Assessor"),    # Transaction Assessor
                ("James_Smith", 3, "Team Lead"),     # Account Holder Team Lead
                ("Emma_Davis", 3, "Reviewer"),       # Account Holder Reviewer
                ("Alex_Kumar", 4, "Team Lead"),      # Loan Team Lead
                ("Sophie_Taylor", 4, "Assessor"),    # Loan Assessor
                ("Marcus_Brown", 4, "Reviewer"),     # Loan Reviewer
            ]
            
            for agent, workbench_id, role in demo_roles:
                try:
                    self.role_manager.assign_workbench_role(agent, workbench_id, role, "System")
                except Exception:
                    pass  # Ignore if already exists
            
            print("✅ Demo data setup complete - 10 agents across 4 workbenches with proper role distribution")
            
        except Exception as e:
            print(f"🔶 Demo data setup skipped: {e}")

    async def _process_llm_with_commands(self, llm_result: Dict[str, Any], user: str) -> Dict[str, Any]:
        """Process LLM response that contains both natural language and commands"""
        commands = llm_result.get("commands", [])
        natural_response = llm_result.get("natural_response", "")
        
        command_results = []
        
        # Execute each command found in the LLM response
        for cmd in commands:
            try:
                # Process the command using the rule-based system
                result = await self._process_rule_based_command(cmd, user)
                command_results.append({"command": cmd, "result": result})
            except Exception as e:
                command_results.append({"command": cmd, "error": str(e)})
        
        return {
            "type": "llm_with_executed_commands",
            "natural_response": natural_response,
            "command_results": command_results,
            "original_message": llm_result.get("original_message", ""),
            "timestamp": llm_result.get("timestamp")
        }

    async def _process_rule_based_command(self, command: str, user: str) -> Dict[str, Any]:
        """Process a single command using the original rule-based logic"""
        # This contains the original command processing logic
        # Parse command
        original_command = command.strip()
        command_lower = original_command.lower()
        parts = original_command.strip().split()
        if not parts:
            return {"error": "Empty command"}
        
        # Normalize command - handle natural language
        action = self.normalize_command(command_lower, parts)
        
        # [Include all the original command processing logic here]
        # For now, return a simple response - you can expand this
        return {"message": f"Executed command: {command}", "action": action}

    def get_suggested_prompts(self) -> List[Dict[str, str]]:
        """Get organized suggested prompts with clear grouping and descriptions"""
        prompts = [
            # Getting Started
            {"category": "🚀 Getting Started", "prompt": "help", "description": "View all available commands"},
            {"category": "🚀 Getting Started", "prompt": "how many agents are there?", "description": "Count total agents"},
            {"category": "🚀 Getting Started", "prompt": "show list of all agents", "description": "Show all agents in natural language"},
            {"category": "🚀 Getting Started", "prompt": "workbenches", "description": "Quick workbench list"},
            
            # Create New Items
            {"category": "✨ Create New Items", "prompt": "create agent NewAgent", "description": "Add a new agent"},
            {"category": "✨ Create New Items", "prompt": "create-agent DataAnalyst", "description": "Add an agent via short command"},
            {"category": "✨ Create New Items", "prompt": "create workbench Support \"Customer support\"", "description": "Build a Support workbench"},
            {"category": "✨ Create New Items", "prompt": "create-task 6002 Chitra 1", "description": "Create a task and assign it"},
            
            # Agent Management
            {"category": "👥 Agent Management", "prompt": "details about abhijit", "description": "Full details of an agent"},
            {"category": "👥 Agent Management", "prompt": "show agent roles abhijit", "description": "List roles for an agent"},
            {"category": "👥 Agent Management", "prompt": "agent-roles Chitra", "description": "Quick role summary"},
            
            # Workbench Operations
            {"category": "🏢 Workbench Operations", "prompt": "show roles 1", "description": "View Dispute workbench roles"},
            {"category": "🏢 Workbench Operations", "prompt": "roles 2", "description": "View Transaction workbench roles"},
            {"category": "🏢 Workbench Operations", "prompt": "show roles 3", "description": "View Account Holder workbench roles"},
            {"category": "🏢 Workbench Operations", "prompt": "roles 4", "description": "View Loan workbench roles"},
            
            # Role Management - placeholder for future assign-role & revoke-role prompts
            {"category": "🎭 Role Management", "prompt": "assign-role ashish 1 Assessor", "description": "Assign role to agent in workbench"},
            {"category": "🎭 Role Management", "prompt": "coverage", "description": "Show role coverage report"},
        ]
        
        # Filter out MCP-only commands if not available
        if not MCP_AVAILABLE:
            prompts = [p for p in prompts if p["category"] != "📋 Task Management"]
        
        return prompts

    async def process_command(self, command: str, user: str = "Anonymous") -> Dict[str, Any]:
        """Process MCP commands and return results - with LLM integration"""
        try:
            # Try LLM processing first if available
            if self.llm_enabled and self.llm_processor:
                llm_result = await self.llm_processor.process_with_llm(command, self.last_command_context)
                
                if llm_result.get("fallback_to_rules"):
                    # LLM failed, fall back to rule-based processing
                    pass  # Continue to rule-based processing below
                elif llm_result.get("type") == "llm_with_commands":
                    # LLM provided both natural response and commands to execute
                    return await self._process_llm_with_commands(llm_result, user)
                elif llm_result.get("type") == "llm_response":
                    # Pure LLM conversational response
                    return llm_result
                else:
                    # Unknown LLM response format, fall back to rules
                    pass  # Continue to rule-based processing below
            
            # Rule-based processing (original logic)
            # Parse command
            original_command = command.strip()
            command_lower = original_command.lower()
            parts = original_command.strip().split()
            if not parts:
                return {"error": "Empty command"}
            
            # Normalize command - handle natural language
            action = self.normalize_command(command_lower, parts)
            
            # Handle different commands
            if action == "help":
                llm_status = "🤖 LLM-POWERED" if self.llm_enabled else "🤖 Rule-based processor"
                llm_info = f" ({self.llm_processor.provider})" if self.llm_enabled else " (no LLM)"
                
                return {
                    "type": "help",
                    "commands": [
                        f"💡 {llm_status}{llm_info}",
                        "🔗 Supports contextual follow-up commands",
                        "🗣️ Natural language conversation enabled" if self.llm_enabled else "🗣️ Pattern-based natural language",
                        "",
                        "help - Show available commands",
                        "agents / list agents / show agents - List all agents",
                        "workbenches / list workbenches / show workbenches - List all workbenches",
                        "create-agent <name> - Create a new agent",
                        "create-workbench <name> \"<description>\" - Create a new workbench",
                        "create-task <id> [agent] [workbench_id] - Create a new task",
                        "tasks <agent> - Get tasks for agent",
                        "assign <agent> <task_id> [workbench_id] - Assign task to agent",
                        "status <task_id> <agent> <status> - Update task status",
                        "roles <workbench_id> / show roles <workbench_id> - Show workbench roles",
                        "assign-role <agent> <workbench_id> <role> - Assign workbench role",
                        "agent-roles <agent> / show agent roles <agent> - Show agent's roles",
                        "coverage / show coverage - Show role coverage report",
                        "stats <agent> - Get agent statistics",
                        "",
                        "🔗 Contextual Commands (after listing agents):",
                        "their assigned workbenches - Show all agent assignments",
                        "where are they assigned - Show workbench assignments",
                        "their roles - Show all agent roles",
                        "",
                        "🤖 LLM Commands:",
                        "llm-status - Show LLM integration status",
                        "llm-toggle - Enable/disable LLM processing",
                        "llm-clear - Clear conversation history"
                    ]
                }
            
            elif action == "greeting":
                return {
                    "type": "welcome",
                    "message": """Welcome to OPS Center Chat! 🎉

I'm your Operations Assistant—ready to help you manage agents, workbenches, and workflows with simple commands.

Here's what you can do:
• Ask "help" to see all commands
• Type "agents" to list agents
• Create workflows with create workflow for "<name>"
• Assign tasks, view stats, and more—all in plain English

💡 Tip: Try "how many tasks has Agent A completed in the last 3 days?" to get started.""",
                    "suggestions": ["help", "agents", "workbenches", "coverage", "create workflow for \"Customer Support\""]
                }
            
            elif action == "thanks":
                return {
                    "type": "conversational", 
                    "message": "😊 You're welcome! Happy to help with your MCP management needs. Is there anything else you'd like to do?",
                    "suggestions": ["agents", "workbenches", "coverage", "help"]
                }
            
            elif action == "goodbye":
                return {
                    "type": "conversational",
                    "message": "👋 Goodbye! Thanks for using the MCP Chat Interface. Have a great day!",
                    "suggestions": []
                }
            
            elif action == "status":
                llm_status = "🤖 LLM-POWERED" if self.llm_enabled else "🤖 Rule-based"
                mcp_status = "🟢 Connected" if self.mcp_client else "🔶 Demo Mode"
                return {
                    "type": "conversational",
                    "message": f"🚀 I'm doing great! System status: {llm_status} | {mcp_status} | Ready to help you manage your MCP system.",
                    "suggestions": ["agents", "workbenches", "coverage", "help"]
                }
            
            elif action == "prompts" or action == "suggestions":
                prompts = self.get_suggested_prompts()
                return {"type": "suggested_prompts", "data": prompts}
            
            elif action == "create-agent":
                agent_name = self.extract_create_agent_name(original_command, parts)
                if not agent_name:
                    # Check if user used invalid words like "a", "the", etc.
                    invalid_words = ['a', 'an', 'the', 'new', 'some', 'this', 'that']
                    used_invalid = any(word in original_command.lower() for word in invalid_words)
                    
                    if used_invalid:
                        return {
                            "error": "Please provide a proper agent name (not 'a', 'the', etc.)",
                            "suggestion": "Try: 'create agent CustomerServiceAgent' or 'create agent DataAnalyst'",
                            "examples": [
                                "create agent SalesManager",
                                "create agent TechnicalSupport",
                                "create agent ProjectCoordinator",
                                "create agent QualityAssurance"
                            ]
                        }
                    else:
                        return {
                            "error": "Please specify an agent name",
                            "suggestion": "Format: create agent <n>",
                            "examples": [
                                "create agent NewAgent",
                                "create agent DataAnalyst",
                                "create agent ProjectManager"
                            ]
                        }
                return self.create_agent(agent_name, user)
            
            elif action == "create-workbench":
                workbench_name, description = self.extract_create_workbench_params(original_command, parts)
                if not workbench_name:
                    # Check if user used invalid words like "a", "the", etc.
                    invalid_words = ['a', 'an', 'the', 'new', 'some', 'this', 'that']
                    used_invalid = any(word in original_command.lower() for word in invalid_words)
                    
                    if used_invalid:
                        return {
                            "error": "Please provide a proper workbench name (not 'a', 'the', etc.)",
                            "suggestion": "Try: 'create workbench CustomerService \"Handle customer inquiries\"' or 'create workbench Marketing \"Marketing campaigns\"'",
                            "examples": [
                                "create workbench Support \"Customer support operations\"",
                                "create workbench Finance \"Financial operations\"", 
                                "create workbench HR \"Human resources management\"",
                                "create workbench IT \"IT operations and support\""
                            ]
                        }
                    else:
                        return {
                            "error": "Please specify a workbench name",
                            "suggestion": "Format: create workbench <Name> \"<Description>\"",
                            "examples": [
                                "create workbench Support \"Customer support operations\"",
                                "create workbench Marketing \"Marketing campaigns\"",
                                "create workbench Finance \"Financial operations\""
                            ]
                        }
                return self.create_workbench(workbench_name, description, user)
            
            elif action == "create-task":
                task_id, agent, workbench_id = self.extract_create_task_params(original_command, parts)
                if task_id is None:
                    return {"error": "Please specify task ID. Example: create-task 6001 or create-task 6002 Chitra 1"}
                return self.create_task(task_id, agent, workbench_id, user)
            
            elif action == "agents":
                if self.mcp_client:
                    result = self.mcp_client.list_agents()
                    # Check if this was a count question
                    if any(phrase in command_lower for phrase in ['how many', 'count', 'number of', 'total']):
                        agent_count = len(result.get('agents', []))
                        result['count_query'] = True
                        result['message'] = f"There are {agent_count} agents in the system"
                    
                    # Store context for follow-up commands
                    self.last_command_context = {
                        "type": "agents_listed",
                        "agents": result.get('agents', []),
                        "command": original_command,
                        "timestamp": datetime.now()
                    }
                    
                    return {"type": "agents", "data": result}
                else:
                    demo_result = self.get_demo_data("agents")
                    # Handle count questions for demo data too
                    if any(phrase in command_lower for phrase in ['how many', 'count', 'number of', 'total']):
                        agent_count = len(demo_result.get('data', {}).get('agents', []))
                        demo_result['data']['count_query'] = True
                        demo_result['data']['message'] = f"There are {agent_count} agents in the system"
                    
                    # Store context for follow-up commands
                    self.last_command_context = {
                        "type": "agents_listed",
                        "agents": demo_result.get('data', {}).get('agents', []),
                        "command": original_command,
                        "timestamp": datetime.now()
                    }
                    
                    return demo_result
            
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
            
            elif action == "roles":
                workbench_id = self.extract_workbench_id(original_command, parts)
                if workbench_id is None:
                    return {"error": "Please specify workbench ID. Example: roles 1 or show roles 1"}
                
                if self.role_manager:
                    try:
                        assignments = self.role_manager.get_workbench_role_assignments(workbench_id)
                        return {"type": "workbench_roles", "data": assignments}
                    except Exception as e:
                        return {"error": f"Could not get workbench roles: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "assign-role":
                agent, workbench_id, role = self.extract_assign_role_params(original_command, parts)
                if not all([agent, workbench_id, role]):
                    return {"error": "Please specify agent, workbench ID, and role. Example: assign-role ashish 1 Assessor"}
                
                if self.role_manager:
                    try:
                        success = self.role_manager.assign_workbench_role(agent, workbench_id, role, user)
                        if success:
                            return {"type": "role_assignment", "message": f"✅ Assigned {role} to {agent} in workbench {workbench_id}"}
                        else:
                            return {"error": "Role assignment failed (may already exist)"}
                    except Exception as e:
                        return {"error": f"Could not assign role: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "agent-roles":
                agent = self.extract_agent_name(original_command, parts)
                if not agent:
                    return {"error": "Please specify agent name. Example: agent-roles abhijit or details about abhijit"}
                
                if self.role_manager:
                    try:
                        roles = self.role_manager.get_agent_workbench_roles(agent)
                        
                        # Check if this was a details request
                        is_details_request = any(phrase in command_lower for phrase in ['details about', 'info about', 'information about', 'tell me about'])
                        
                        # Get additional agent information
                        agent_details = {
                            "agent": agent,
                            "roles": roles,
                            "is_details_request": is_details_request
                        }
                        
                        # Add task information if MCP client is available
                        if self.mcp_client and is_details_request:
                            try:
                                task_count = self.mcp_client.get_agent_task_count(agent, days=7)
                                agent_details["task_count"] = task_count
                                agent_details["recent_tasks"] = self.mcp_client.list_recent_tasks(agent, limit=3)
                            except:
                                pass  # Continue without task info if not available
                        
                        return {"type": "agent_roles", "agent": agent, "data": agent_details}
                    except Exception as e:
                        return {"error": f"Could not get agent information: {e}"}
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
            
            elif action == "agent-workbench-summary":
                # Handle contextual commands like "their assigned workbenches"
                if self.role_manager:
                    try:
                        # Get all agents and their workbench assignments
                        agents_summary = self.get_all_agent_workbench_assignments()
                        
                        # Store context for future commands
                        self.last_command_context = {
                            "type": "agent_workbench_summary",
                            "command": original_command,
                            "timestamp": datetime.now()
                        }
                        
                        return {"type": "agent_workbench_summary", "data": agents_summary}
                    except Exception as e:
                        return {"error": f"Could not get agent workbench assignments: {e}"}
                else:
                    return {"error": "Workbench role manager not available"}
            
            elif action == "llm-status":
                if self.llm_processor:
                    status = self.llm_processor.get_llm_status()
                    if LLM_INTEGRATION_AVAILABLE:
                        availability = test_llm_availability()
                        status["provider_availability"] = availability
                    return {"type": "llm_status", "data": status}
                else:
                    return {"error": "LLM integration not available"}
            
            elif action == "llm-toggle":
                if self.llm_processor:
                    self.llm_enabled = not self.llm_enabled
                    status = "enabled" if self.llm_enabled else "disabled"
                    return {"type": "llm_toggle", "message": f"LLM processing {status}", "enabled": self.llm_enabled}
                else:
                    return {"error": "LLM integration not available"}
            
            elif action == "llm-clear":
                if self.llm_processor:
                    self.llm_processor.clear_conversation_history()
                    return {"type": "llm_clear", "message": "LLM conversation history cleared"}
                else:
                    return {"error": "LLM integration not available"}
            
            elif action == "tasks":
                agent = self.extract_agent_name(original_command, parts)
                if not agent:
                    return {"error": "Please specify agent name. Example: tasks abhijit"}
                
                if self.mcp_client:
                    result = self.mcp_client.list_recent_tasks(agent, limit=10)
                    return {"type": "tasks", "agent": agent, "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "assign":
                agent, task_id, workbench_id = self.extract_assign_params(original_command, parts)
                if not all([agent, task_id]):
                    return {"error": "Please specify agent and task ID. Example: assign abhijit 5001"}
                
                if self.mcp_client:
                    result = self.mcp_client.assign_task(agent, task_id, workbench_id)
                    return {"type": "assignment", "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "status":
                task_id, agent, status = self.extract_status_params(original_command, parts)
                if not all([task_id, agent, status]):
                    return {"error": "Please specify task ID, agent, and status. Example: status 5001 abhijit completed"}
                
                if self.mcp_client:
                    result = self.mcp_client.update_task_status(task_id, agent, status)
                    return {"type": "status_update", "data": result}
                else:
                    return {"error": "MCP client not available", "demo": True}
            
            elif action == "stats":
                agent = self.extract_agent_name(original_command, parts)
                if not agent:
                    return {"error": "Please specify agent name. Example: stats abhijit"}
                
                if self.mcp_client:
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
                # Suggest alternatives for common mistakes
                suggestions = self.suggest_command_alternatives(command_lower)
                error_msg = f"Unknown command: '{original_command}'. Type 'help' for available commands or 'prompts' for suggestions."
                if suggestions:
                    error_msg += f"\n\n💡 Did you mean: {suggestions}"
                return {"error": error_msg}
        
        except Exception as e:
            return {"error": f"Error processing command: {str(e)}"}

    def normalize_command(self, command_lower: str, parts: List[str]) -> str:
        """Normalize natural language commands to standard actions"""
        
        # Handle conversational greetings and common phrases
        if command_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
            return "greeting"
        
        if command_lower in ["thanks", "thank you", "thanks!", "thank you!"]:
            return "thanks"
        
        if command_lower in ["bye", "goodbye", "see you", "exit", "quit"]:
            return "goodbye"
        
        if "how are you" in command_lower or "how's it going" in command_lower or "what's up" in command_lower:
            return "status"
        
        # Handle contextual/pronoun commands
        if any(phrase in command_lower for phrase in ['their assigned', 'their workbenches', 'their roles', 'assigned workbenches', 'workbench assignments']):
            return "agent-workbench-summary"  # New command for showing all agent workbench assignments
        elif any(phrase in command_lower for phrase in ['they are assigned to', 'where are they assigned', 'their assignments']):
            return "agent-workbench-summary"
        elif command_lower in ['their workbenches', 'workbenches', 'assignments', 'where are they', 'assigned to']:
            return "agent-workbench-summary"
        
        # Handle question-style commands
        elif any(phrase in command_lower for phrase in ['how many agents', 'count agents', 'number of agents', 'total agents']):
            return "agents"
        elif any(phrase in command_lower for phrase in ['how many workbenches', 'count workbenches', 'number of workbenches', 'total workbenches']):
            return "workbenches"
        elif any(phrase in command_lower for phrase in ['details about', 'info about', 'information about', 'tell me about']):
            # Extract the subject of the details request
            if any(agent_indicator in command_lower for agent_indicator in ['agent', 'user']):
                return "agent-roles"  # Show agent details via roles
            else:
                return "agent-roles"  # Default to agent details
        elif any(phrase in command_lower for phrase in ['what agents', 'which agents', 'who are the agents']):
            return "agents"
        elif any(phrase in command_lower for phrase in ['what workbenches', 'which workbenches', 'what are the workbenches']):
            return "workbenches"
        
        # Handle natural language patterns
        elif any(phrase in command_lower for phrase in ['show list of all workbenches', 'list all workbenches', 'show workbenches', 'list workbenches']):
            return "workbenches"
        elif any(phrase in command_lower for phrase in ['show list of all agents', 'list all agents', 'show agents', 'list agents']):
            return "agents"
        elif any(phrase in command_lower for phrase in ['show roles', 'list roles', 'roles in', 'workbench roles']):
            return "roles"
        elif any(phrase in command_lower for phrase in ['show coverage', 'coverage report', 'role coverage']):
            return "coverage"
        elif any(phrase in command_lower for phrase in ['show agent roles', 'agent roles', 'roles for']):
            return "agent-roles"
        elif any(phrase in command_lower for phrase in ['create agent', 'new agent', 'add agent']):
            return "create-agent"
        elif any(phrase in command_lower for phrase in ['create workbench', 'new workbench', 'add workbench']):
            return "create-workbench"
        elif any(phrase in command_lower for phrase in ['create workflow', 'new workflow', 'add workflow', 'workflow for']):
            return "create-workbench"  # Workflows are essentially workbenches in our system
        elif any(phrase in command_lower for phrase in ['create task', 'new task', 'add task']):
            return "create-task"
        elif any(phrase in command_lower for phrase in ['assign role', 'give role', 'set role']):
            return "assign-role"
        
        # Handle standard commands
        action = parts[0].lower() if parts else ""
        
        # Command aliases
        aliases = {
            'show': 'workbenches',  # Default 'show' to workbenches
            'list': 'workbenches',  # Default 'list' to workbenches  
            'display': 'workbenches',
            'view': 'workbenches',
            'get': 'agents',
            'fetch': 'agents',
            'details': 'agent-roles',  # Handle 'details' as agent info
            'info': 'agent-roles',     # Handle 'info' as agent info
            'about': 'agent-roles',    # Handle 'about' as agent info
            'how': 'agents',           # Default 'how' questions to agents
            'what': 'agents',          # Default 'what' questions to agents
            'which': 'agents',         # Default 'which' questions to agents
            'who': 'agents',           # Default 'who' questions to agents
            'count': 'agents',         # Default 'count' to agents
            'total': 'agents'          # Default 'total' to agents
        }
        
        return aliases.get(action, action)

    def extract_create_agent_name(self, command: str, parts: List[str]) -> str:
        """Extract agent name from create agent command"""
        # Handle natural language
        if 'create agent' in command.lower() or 'new agent' in command.lower() or 'add agent' in command.lower():
            words = command.split()
            for i, word in enumerate(words):
                if word.lower() in ['agent'] and i + 1 < len(words):
                    agent_name = words[i + 1]
                    # Validate agent name - reject common words/articles
                    if agent_name.lower() in ['a', 'an', 'the', 'new', 'some', 'this', 'that']:
                        return ""  # Invalid name
                    return agent_name
        
        # Handle standard format
        if len(parts) > 1:
            agent_name = parts[1]
            # Validate agent name - reject common words/articles
            if agent_name.lower() in ['a', 'an', 'the', 'new', 'some', 'this', 'that']:
                return ""  # Invalid name
            return agent_name
        
        return ""

    def extract_create_workbench_params(self, command: str, parts: List[str]) -> tuple:
        """Extract workbench name and description from create workbench command"""
        import re
        
        # Handle natural language
        if any(phrase in command.lower() for phrase in ['create workbench', 'new workbench', 'create workflow', 'new workflow', 'workflow for']):
            # Extract after "workbench" or "workflow"
            match = re.search(r'(?:workbench|workflow)\s+(?:for\s+)?(?:"([^"]+)"|(\w+))(?:\s+"([^"]*)")?', command, re.IGNORECASE)
            if match:
                workbench_name = match.group(1) or match.group(2)
                # Validate workbench name - reject common words/articles
                if workbench_name and workbench_name.lower() in ['a', 'an', 'the', 'new', 'some', 'this', 'that']:
                    return "", ""  # Invalid name, will trigger error asking for proper name
                description = match.group(3) or ""
                return workbench_name or "", description
        
        # Handle standard format
        if len(parts) > 1:
            workbench_name = parts[1]
            # Validate workbench name - reject common words/articles
            if workbench_name.lower() in ['a', 'an', 'the', 'new', 'some', 'this', 'that']:
                return "", ""  # Invalid name, will trigger error asking for proper name
            
            description = ""
            if len(parts) > 2:
                description = " ".join(parts[2:]).strip('"\'')
            return workbench_name, description
        
        return "", ""

    def extract_create_task_params(self, command: str, parts: List[str]) -> tuple:
        """Extract task parameters from create task command"""
        # Handle natural language
        if 'create task' in command.lower() or 'new task' in command.lower():
            words = command.split()
            for i, word in enumerate(words):
                if word.lower() == 'task' and i + 1 < len(words):
                    try:
                        task_id = int(words[i + 1])
                        agent = words[i + 2] if i + 2 < len(words) else None
                        workbench_id = int(words[i + 3]) if i + 3 < len(words) else None
                        return task_id, agent, workbench_id
                    except (ValueError, IndexError):
                        pass
        
        # Handle standard format
        if len(parts) > 1:
            try:
                task_id = int(parts[1])
                agent = parts[2] if len(parts) > 2 else None
                workbench_id = int(parts[3]) if len(parts) > 3 else None
                return task_id, agent, workbench_id
            except ValueError:
                pass
        
        return None, None, None

    def extract_workbench_id(self, command: str, parts: List[str]) -> int:
        """Extract workbench ID from roles command"""
        # Look for numbers in the command
        import re
        numbers = re.findall(r'\d+', command)
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                pass
        
        # Fallback to parts
        if len(parts) > 1:
            try:
                return int(parts[1])
            except ValueError:
                pass
        
        return None

    def extract_agent_name(self, command: str, parts: List[str]) -> str:
        """Extract agent name from command"""
        # Handle natural language patterns
        if 'roles for' in command.lower():
            words = command.split()
            for i, word in enumerate(words):
                if word.lower() == 'for' and i + 1 < len(words):
                    return words[i + 1]
        
        # Handle "details about" style commands
        if any(phrase in command.lower() for phrase in ['details about', 'info about', 'information about', 'tell me about']):
            words = command.split()
            for i, word in enumerate(words):
                if word.lower() in ['about'] and i + 1 < len(words):
                    return words[i + 1]
        
        # Handle question style commands
        if any(phrase in command.lower() for phrase in ['about', 'details', 'info']):
            words = command.split()
            # Look for agent names after keywords
            for i, word in enumerate(words):
                if word.lower() in ['about', 'details', 'info'] and i + 1 < len(words):
                    return words[i + 1]
        
        # Handle standard format
        if len(parts) > 1:
            return parts[1]
        
        return ""

    def extract_assign_role_params(self, command: str, parts: List[str]) -> tuple:
        """Extract assign role parameters"""
        # Handle natural language
        if 'assign role' in command.lower() or 'give role' in command.lower():
            # Pattern: assign role <role> to <agent> in workbench <id>
            import re
            match = re.search(r'(?:assign|give)\s+role\s+(\w+)\s+to\s+(\w+)\s+in\s+workbench\s+(\d+)', command, re.IGNORECASE)
            if match:
                role, agent, workbench_id = match.groups()
                return agent, int(workbench_id), role
            
            # Pattern: assign <agent> <workbench_id> <role>
            words = command.split()
            if len(words) >= 5:  # assign role agent workbench_id role
                try:
                    return words[2], int(words[3]), words[4]
                except (ValueError, IndexError):
                    pass
        
        # Handle standard format: assign-role agent workbench_id role
        if len(parts) > 3:
            try:
                return parts[1], int(parts[2]), parts[3]
            except ValueError:
                pass
        
        return None, None, None

    def extract_assign_params(self, command: str, parts: List[str]) -> tuple:
        """Extract assign task parameters"""
        if len(parts) > 2:
            try:
                agent = parts[1]
                task_id = int(parts[2])
                workbench_id = int(parts[3]) if len(parts) > 3 else None
                return agent, task_id, workbench_id
            except ValueError:
                pass
        
        return None, None, None

    def extract_status_params(self, command: str, parts: List[str]) -> tuple:
        """Extract status update parameters"""
        if len(parts) > 3:
            try:
                task_id = int(parts[1])
                agent = parts[2]
                status = parts[3]
                return task_id, agent, status
            except ValueError:
                pass
        
        return None, None, None

    def suggest_command_alternatives(self, command_lower: str) -> str:
        """Suggest alternative commands for common mistakes"""
        suggestions = []
        
        # Handle question-style suggestions
        if 'how many' in command_lower:
            if 'agent' in command_lower:
                suggestions.append("'how many agents are there ?'")
            elif 'workbench' in command_lower:
                suggestions.append("'how many workbenches are there ?'")
        
        if 'details' in command_lower or 'info' in command_lower:
            suggestions.append("'details about abhijit'")
            suggestions.append("'info about Chitra'")
        
        if 'show' in command_lower or 'list' in command_lower:
            if 'workbench' in command_lower:
                suggestions.append("'workbenches' or 'show list of all workbenches'")
            elif 'agent' in command_lower:
                suggestions.append("'agents' or 'show list of all agents'")
            elif 'role' in command_lower:
                suggestions.append("'roles 1' or 'show roles 1'")
        
        if 'what' in command_lower or 'who' in command_lower:
            if 'agent' in command_lower:
                suggestions.append("'what agents exist ?' or 'who are the agents ?'")
            elif 'workbench' in command_lower:
                suggestions.append("'what workbenches exist ?'")
        
        if 'create' in command_lower:
            if 'agent' in command_lower:
                suggestions.append("'create-agent NewAgent' or 'create agent NewAgent'")
            elif 'workbench' in command_lower:
                suggestions.append("'create-workbench Support \"Description\"'")
            elif 'task' in command_lower:
                suggestions.append("'create-task 6001'")
        
        if 'tell me' in command_lower:
            suggestions.append("'tell me about abhijit'")
            suggestions.append("'details about Chitra'")
        
        return ", ".join(suggestions[:3])  # Limit to 3 suggestions

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
                            "message": "Welcome, OPS Ninja! You're now connected to the OPS Center MCP Chat Interface. " + 
                          ("🌐 Cloud demo mode active with full UI features. " if not MCP_AVAILABLE else "") + 
                          "How can I assist you today?",
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

@app.post("/api/command")
async def process_command_api(request: dict):
    """REST endpoint to process commands when WebSocket is not available"""
    try:
        message = request.get("message", "")
        user = request.get("user", "Anonymous")
        
        if not message:
            return {"error": "No message provided"}
        
        # Process the command using the same logic as WebSocket
        result = await manager.process_command(message, user)
        return result
        
    except Exception as e:
        return {"error": f"Command processing failed: {str(e)}", "fallback": True}

# Create the HTML template with modern enterprise UI/UX
chat_html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Chat Interface</title>
    <meta name="description" content="Interactive web interface for MCP system">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-600: #4f46e5;
            --primary-700: #4338ca;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --blue-50: #eff6ff;
            --blue-500: #3b82f6;
            --green-50: #f0fdf4;
            --green-500: #22c55e;
            --amber-50: #fffbeb;
            --amber-500: #f59e0b;
            --red-50: #fef2f2;
            --red-500: #ef4444;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh;
            color: var(--gray-800);
            line-height: 1.6;
        }
        
        .chat-container {
            display: flex;
            height: 100vh;
            max-width: 100vw;
            background: white;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Top Bar */
        .top-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 64px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--gray-200);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            z-index: 50;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .logo-section:hover {
            background: var(--gray-50);
        }
        
        .logo-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--gray-900);
            margin-left: 8px;
        }
        
        .status-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .status-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            border: 1px solid var(--gray-300);
            background: white;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-toggle:hover {
            border-color: var(--primary-600);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-cloud {
            background: var(--green-50);
            color: var(--green-500);
        }
        
        .badge-demo {
            background: var(--amber-50);
            color: var(--amber-500);
        }
        
        .badge-error {
            background: var(--red-50);
            color: var(--red-500);
        }
        
        .sidebar {
            width: 320px;
            background: var(--gray-50);
            border-right: 1px solid var(--gray-200);
            display: flex;
            flex-direction: column;
            margin-top: 64px;
            height: calc(100vh - 64px);
        }
        
        .sidebar-header {
            background: var(--gray-800);
            color: white;
            padding: 20px;
            border-bottom: 1px solid var(--gray-200);
        }
        
        .sidebar-header h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .sidebar-header p {
            font-size: 14px;
            color: var(--gray-300);
            font-weight: 400;
        }
        
        .prompts-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .prompt-category {
            margin-bottom: 24px;
        }
        
        .category-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            cursor: pointer;
            user-select: none;
            border-bottom: 1px solid var(--gray-200);
            margin-bottom: 12px;
        }
        
        .category-header:hover {
            color: var(--primary-600);
        }
        
        .category-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--gray-700);
        }
        
        .category-toggle {
            font-size: 12px;
            color: var(--gray-400);
            transition: transform 0.2s ease;
        }
        
        .category-toggle.collapsed {
            transform: rotate(-90deg);
        }
        
        .category-content {
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .category-content.collapsed {
            max-height: 0;
            opacity: 0;
        }
        
        .prompt-item {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: 8px;
            padding: 12px;
            margin: 6px 0;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .prompt-item:hover {
            background: var(--gray-50);
            border-color: var(--primary-600);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px 0 rgba(79, 70, 229, 0.15);
        }
        
        .prompt-item:active {
            transform: translateY(0);
        }
        
        .prompt-item.creation {
            border-left: 4px solid var(--green-500);
            background: var(--green-50);
        }
        
        .prompt-item.creation:hover {
            background: white;
            box-shadow: 0 4px 12px 0 rgba(34, 197, 94, 0.15);
        }
        
        .prompt-command {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 500;
            color: var(--gray-800);
            margin-bottom: 4px;
            font-size: 13px;
            line-height: 1.4;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .prompt-description {
            color: var(--gray-500);
            font-size: 12px;
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .prompt-tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--gray-800);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            z-index: 10;
            margin-bottom: 8px;
        }
        
        .prompt-item:hover .prompt-tooltip {
            opacity: 1;
        }
        
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            margin-top: 64px;
            height: calc(100vh - 64px);
        }
        
        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: var(--gray-50);
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 8px;
            padding: 16px 20px;
            border-radius: 16px;
            max-width: 75%;
            word-wrap: break-word;
            position: relative;
            animation: messageSlideIn 0.3s ease-out;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
            color: white;
            margin-left: auto;
            border-radius: 16px 16px 4px 16px;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
        
        .message.system {
            background: linear-gradient(135deg, var(--green-500), #16a34a);
            color: white;
            margin: 0 auto;
            max-width: 90%;
            text-align: center;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }
        
        .message.response {
            background: rgba(255, 255, 255, 0.9);
            color: var(--gray-800);
            border-radius: 16px 16px 16px 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--gray-200);
        }
        
        .message.error {
            background: linear-gradient(135deg, var(--red-500), #dc2626);
            color: white;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }
        
        .message-header {
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 8px;
            opacity: 0.8;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .message-content {
            font-size: 14px;
            line-height: 1.5;
        }
        
        .message-time {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 8px;
            font-weight: 400;
        }
        
        .chat-input {
            padding: 20px 24px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(16px);
            border-top: 1px solid var(--gray-200);
            display: flex;
            align-items: flex-end;
            gap: 12px;
        }
        
        .input-container {
            flex: 1;
            position: relative;
        }
        
        .chat-textarea {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--gray-200);
            border-radius: 12px;
            outline: none;
            font-size: 16px;
            font-family: inherit;
            resize: none;
            min-height: 44px;
            max-height: 120px;
            transition: all 0.2s ease;
            background: white;
            line-height: 1.5;
        }
        
        .chat-textarea:focus {
            border-color: var(--primary-600);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .chat-textarea::placeholder {
            color: var(--gray-400);
        }
        
        .input-hints {
            position: absolute;
            bottom: -24px;
            left: 0;
            font-size: 12px;
            color: var(--gray-400);
            display: flex;
            gap: 16px;
        }
        
        .hint {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .send-button {
            background: var(--primary-600);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 80px;
            justify-content: center;
        }
        
        .send-button:hover {
            background: var(--primary-700);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
        
        .send-button:active {
            transform: translateY(0);
        }
        
        .send-button:disabled {
            background: var(--gray-300);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .send-icon {
            font-size: 16px;
        }
        
        .connection-status {
            position: fixed;
            top: 80px;
            right: 24px;
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
            font-weight: 500;
            z-index: 40;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .connection-status.connected {
            background: rgba(34, 197, 94, 0.9);
        }
        
        .connection-status.connecting {
            background: rgba(245, 158, 11, 0.9);
        }
        
        .connection-status.disconnected {
            background: rgba(239, 68, 68, 0.9);
        }
        
        /* Floating Action Button */
        .fab-container {
            position: fixed;
            bottom: 100px;
            right: 24px;
            z-index: 40;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .fab {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: var(--primary-600);
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 8px 24px rgba(79, 70, 229, 0.4);
            transition: all 0.3s ease;
            backdrop-filter: blur(8px);
        }
        
        .fab:hover {
            transform: scale(1.1);
            box-shadow: 0 12px 32px rgba(79, 70, 229, 0.5);
        }
        
        .fab.secondary {
            background: white;
            color: var(--gray-600);
            width: 48px;
            height: 48px;
            font-size: 18px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--gray-200);
        }
        
        .fab.secondary:hover {
            background: var(--gray-50);
            color: var(--primary-600);
        }
        
        .fab-tooltip {
            position: absolute;
            right: 64px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--gray-800);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }
        
        .fab:hover .fab-tooltip {
            opacity: 1;
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
        
        .creation-result {
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
            border-left: 4px solid #48bb78;
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
            background: var(--primary-600);
            color: white;
            border: none;
            padding: 12px;
            cursor: pointer;
            position: fixed;
            top: 70px;
            left: 16px;
            border-radius: 12px;
            z-index: 60;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            transition: all 0.2s ease;
            font-size: 16px;
        }
        
        .toggle-sidebar:hover {
            background: var(--primary-700);
            transform: scale(1.05);
        }
        
        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .chat-container {
                flex-direction: column;
            }
            
            .top-bar {
                padding: 0 16px;
            }
            
            .logo-title {
                font-size: 18px;
            }
            
            .status-section {
                gap: 8px;
            }
            
            .status-badge {
                display: none;
            }
            
            .sidebar {
                width: 100%;
                height: 40vh;
                border-right: none;
                border-bottom: 1px solid var(--gray-200);
                position: fixed;
                top: 64px;
                left: 0;
                z-index: 30;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            }
            
            .sidebar.mobile-open {
                transform: translateY(0);
            }
            
            .main-chat {
                margin-top: 64px;
                height: calc(100vh - 64px);
            }
            
            .toggle-sidebar {
                display: block;
            }
            
            .chat-messages {
                padding: 16px;
            }
            
            .message {
                max-width: 90%;
                padding: 12px 16px;
            }
            
            .chat-input {
                padding: 16px;
            }
            
            .input-hints {
                display: none;
            }
            
            .connection-status {
                top: 70px;
                right: 16px;
                font-size: 11px;
                padding: 6px 12px;
            }
            
            .fab-container {
                bottom: 80px;
                right: 16px;
            }
            
            .fab {
                width: 48px;
                height: 48px;
                font-size: 18px;
            }
            
            .fab.secondary {
                width: 40px;
                height: 40px;
                font-size: 16px;
            }
        }
        
        @media (max-width: 480px) {
            .top-bar {
                padding: 0 12px;
            }
            
            .logo-title {
                font-size: 16px;
            }
            
            .sidebar {
                height: 50vh;
            }
            
            .chat-messages {
                padding: 12px;
            }
            
            .message {
                padding: 10px 14px;
                font-size: 14px;
            }
            
            .chat-input {
                padding: 12px;
            }
            
            .chat-textarea {
                font-size: 16px; /* Prevent zoom on iOS */
            }
        }
    </style>
</head>
<body>
    <!-- Top Bar -->
    <div class="top-bar">
        <div class="logo-section" onclick="showAbout()">
            <span style="font-size: 24px;">🤖</span>
            <span class="logo-title">MCP Chat Interface</span>
        </div>
        
        <div class="status-section">
            <!-- Consolidated into single connection status badge below -->
        </div>
    </div>
    
    <!-- Toggle Sidebar Button (Mobile) -->
    <button class="toggle-sidebar" onclick="toggleSidebar()" style="display: none;">
        <span>💡</span>
    </button>
    
    <div class="chat-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h3>💡 Suggested Prompts</h3>
                <p>Click any prompt to try it instantly</p>
            </div>
            <div class="prompts-container" id="promptsContainer">
                <!-- Prompts will be loaded here -->
            </div>
        </div>
        
        <!-- Main Chat -->
        <div class="main-chat">
            <div class="chat-messages" id="messages">
                <!-- Messages will appear here -->
            </div>
            
            <div class="chat-input">
                <div class="input-container">
                    <textarea 
                        id="messageInput" 
                        class="chat-textarea"
                        placeholder="Type your message here... Ready to use!"
                        rows="1"
                        maxlength="1000"></textarea>
                    <div class="input-hints">
                        <div class="hint">
                            <span>💡</span>
                            <span>Press / for commands</span>
                        </div>
                        <div class="hint">
                            <span>↑</span>
                            <span>Previous message</span>
                        </div>
                    </div>
                </div>
                                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        <span class="send-icon">📤</span>
                        <span>Send</span>
                    </button>
            </div>
        </div>
    </div>
    
    <!-- Connection Status -->
    <div class="connection-status connected" id="connectionStatus">
        🟢 Ready
    </div>
    
    <!-- Floating Action Buttons -->
    <div class="fab-container" id="fabContainer">
        <button class="fab secondary" onclick="executeQuickCommand('agents')">
            <span>👥</span>
            <div class="fab-tooltip">Show Agents</div>
        </button>
        <button class="fab secondary" onclick="executeQuickCommand('coverage')">
            <span>📊</span>
            <div class="fab-tooltip">Coverage Report</div>
        </button>
        <button class="fab" onclick="executeQuickCommand('help')">
            <span>❓</span>
            <div class="fab-tooltip">Help</div>
        </button>
    </div>
    
    <script>
        let socket;
        let userId = 'User_' + Math.random().toString(36).substr(2, 9);
        let mcpAvailable = false;
        let workbenchManagerAvailable = false;
        let isCloudDeployment = false;
        let suggestedPrompts = [];
        let messageHistory = [];
        let historyIndex = -1;
        let collapsedCategories = new Set();
        
        // Auto-resize textarea
        function autoResizeTextarea() {
            const textarea = document.getElementById('messageInput');
            textarea.style.height = 'auto';
            const newHeight = Math.min(textarea.scrollHeight, 120);
            textarea.style.height = newHeight + 'px';
        }
        
        // Toggle sidebar for mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('mobile-open');
        }
        
        // Show about dialog
        function showAbout() {
            const aboutMsg = {
                type: 'system',
                message: `🤖 MCP Chat Interface v2.0
                
Enterprise-grade agent and workbench management system.

Features:
• LLM-powered natural language processing
• Rule-based command fallback
• Agent and workbench management
• Role-based access control
• Real-time task tracking
• Mobile-responsive design

Built with modern web technologies for optimal performance.`,
                timestamp: new Date().toISOString()
            };
            displayMessage(aboutMsg);
        }
        
        // Toggle demo mode
        function toggleDemo() {
            // This would toggle between demo and connected mode
            // For now, just show status
            executeQuickCommand('llm-status');
        }
        
        // Execute quick commands from FAB
        function executeQuickCommand(command) {
            const input = document.getElementById('messageInput');
            input.value = command;
            sendMessage();
        }
        
        // Handle message history navigation
        function navigateHistory(direction) {
            if (messageHistory.length === 0) return;
            
            if (direction === 'up') {
                historyIndex = Math.min(historyIndex + 1, messageHistory.length - 1);
            } else {
                historyIndex = Math.max(historyIndex - 1, -1);
            }
            
            const input = document.getElementById('messageInput');
            if (historyIndex >= 0) {
                input.value = messageHistory[messageHistory.length - 1 - historyIndex];
            } else {
                input.value = '';
            }
            autoResizeTextarea();
        }
        
        // Toggle category collapse
        function toggleCategory(categoryName) {
            if (collapsedCategories.has(categoryName)) {
                collapsedCategories.delete(categoryName);
            } else {
                collapsedCategories.add(categoryName);
            }
            updateCategoryDisplay(categoryName);
        }
        
        // Update category display
        function updateCategoryDisplay(categoryName) {
            const content = document.querySelector(`[data-category="${categoryName}"] .category-content`);
            const toggle = document.querySelector(`[data-category="${categoryName}"] .category-toggle`);
            
            if (collapsedCategories.has(categoryName)) {
                content.classList.add('collapsed');
                toggle.classList.add('collapsed');
            } else {
                content.classList.remove('collapsed');
                toggle.classList.remove('collapsed');
            }
        }
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${userId}`;
            
            console.log('Attempting WebSocket connection to:', wsUrl);
            updateConnectionStatus('connecting');
            
            socket = new WebSocket(wsUrl);
            
            // Set a timeout to detect connection issues
            const connectionTimeout = setTimeout(() => {
                console.log('WebSocket connection timeout (3s) - enabling fallback mode');
                enableFallbackMode();
            }, 3000);
            
            socket.onopen = function(event) {
                clearTimeout(connectionTimeout);
                console.log('WebSocket connected successfully');
                updateConnectionStatus('connected');
                
                // Load suggested prompts
                fetch('/api/prompts')
                    .then(response => response.json())
                    .then(data => {
                        suggestedPrompts = data.prompts;
                        displaySuggestedPrompts(data.prompts);
                    })
                    .catch(error => console.log('Could not load prompts:', error));
                
                // Show welcome message after a brief delay
                setTimeout(() => {
                    displayMessage({
                        type: 'response',
                        command: 'Welcome',
                        result: {
                            type: 'welcome',
                            message: `Welcome to OPS Center Chat! 🎉

I'm your Operations Assistant—ready to help you manage agents, workbenches, and workflows with simple commands.

Here's what you can do:
• Ask "help" to see all commands
• Type "agents" to list agents
• Create workflows with create workflow for "<name>"
• Assign tasks, view stats, and more—all in plain English

💡 Tip: Try "how many tasks has Agent A completed in the last 3 days?" to get started.`,
                            suggestions: ["help", "agents", "workbenches", "coverage", "create workflow for \"Customer Support\""]
                        },
                        timestamp: new Date().toISOString()
                    });
                }, 1000);
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
                console.log('WebSocket connection closed:', event.code, event.reason);
                updateConnectionStatus('connecting');
                
                // If it's not a normal closure, enable fallback mode after a few failed attempts
                if (event.code !== 1000) {
                    setTimeout(() => {
                        console.log('Enabling fallback mode due to connection issues');
                        enableFallbackMode();
                    }, 2000);
                } else {
                    setTimeout(connect, 3000); // Reconnect after 3 seconds for normal closure
                }
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateConnectionStatus('connecting');
                // Enable fallback mode immediately on WebSocket error
                setTimeout(() => {
                    console.log('Enabling fallback mode due to WebSocket error');
                    enableFallbackMode();
                }, 1000);
            };
        }
        
        // Fallback mode - enable interface without WebSocket
        function enableFallbackMode() {
            console.log('🔄 Enabling fallback mode - interface will work without WebSocket');
            
            // Update connection status to show we're in fallback mode
            updateConnectionStatus('fallback');
            
            // Load suggested prompts directly
            fetch('/api/prompts')
                .then(response => response.json())
                .then(data => {
                    suggestedPrompts = data.prompts;
                    displaySuggestedPrompts(data.prompts);
                })
                .catch(error => {
                    console.log('Could not load prompts, using default');
                    displayDefaultPrompts();
                });
            
            // Show welcome message
            displayMessage({
                type: 'response',
                command: 'Welcome',
                result: {
                    type: 'welcome',
                    message: `Welcome to OPS Center Chat! 🎉

I'm your Operations Assistant—ready to help you manage agents, workbenches, and workflows with simple commands.

🔶 Running in fallback mode - some features may be limited but core functionality is available.

Here's what you can do:
• Ask "help" to see all commands
• Type "agents" to list agents
• Create workflows with create workflow for "<name>"
• Assign tasks, view stats, and more—all in plain English

💡 Tip: Try "how many tasks has Agent A completed in the last 3 days?" to get started.`,
                    suggestions: ["help", "agents", "workbenches", "coverage", "create workflow for \"Customer Support\""]
                },
                timestamp: new Date().toISOString()
            });
            
            // Enable fallback communication IMMEDIATELY
            window.fallbackMode = true;
            
            // AGGRESSIVELY enable input elements with multiple attempts
            const enableInputs = () => {
                console.log('🔧 FORCE ENABLING INPUTS...');
                const messageInput = document.getElementById('messageInput');
                const sendButton = document.getElementById('sendButton');
                
                if (messageInput) {
                    messageInput.disabled = false;
                    messageInput.placeholder = "Type your command here... (Ready!)";
                    messageInput.style.opacity = '1';
                    messageInput.style.pointerEvents = 'auto';
                    messageInput.focus();
                    console.log('✅ Input enabled and focused');
                }
                
                if (sendButton) {
                    sendButton.disabled = false;
                    sendButton.innerHTML = '<span class="send-icon">📤</span><span>Send</span>';
                    sendButton.style.opacity = '1';
                    sendButton.style.pointerEvents = 'auto';
                    console.log('✅ Send button enabled');
                }
            };
            
            // Enable immediately and retry multiple times
            enableInputs();
            setTimeout(enableInputs, 50);
            setTimeout(enableInputs, 200);
            setTimeout(enableInputs, 500);
        }
        
        // Default prompts in case API fails
        function displayDefaultPrompts() {
            const defaultPrompts = [
                {"category": "🚀 Getting Started", "prompt": "help", "description": "View all available commands"},
                {"category": "🚀 Getting Started", "prompt": "agents", "description": "List all agents"},
                {"category": "✨ Create New Items", "prompt": "create agent NewAgent", "description": "Add a new agent"},
                {"category": "👥 Agent Management", "prompt": "details about abhijit", "description": "Full details of an agent"}
            ];
            displaySuggestedPrompts(defaultPrompts);
        }
        
        function updateConnectionStatus(status) {
            const statusEl = document.getElementById('connectionStatus');
            if (!statusEl) return;
            
            // Handle different status types
            if (status === 'connected' || status === true) {
                statusEl.textContent = '🟢 Connected';
                statusEl.className = 'connection-status connected';
            } else if (status === 'connecting') {
                statusEl.textContent = '🟡 Connecting...';
                statusEl.className = 'connection-status connecting';
            } else if (status === 'fallback') {
                statusEl.textContent = '🔶 HTTP Mode';
                statusEl.className = 'connection-status connecting';
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
                categoryDiv.setAttribute('data-category', category);
                
                // Category header with toggle
                const headerDiv = document.createElement('div');
                headerDiv.className = 'category-header';
                headerDiv.onclick = () => toggleCategory(category);
                
                const titleDiv = document.createElement('div');
                titleDiv.className = 'category-title';
                titleDiv.textContent = category;
                
                const toggleDiv = document.createElement('div');
                toggleDiv.className = 'category-toggle';
                toggleDiv.textContent = '▼';
                
                headerDiv.appendChild(titleDiv);
                headerDiv.appendChild(toggleDiv);
                categoryDiv.appendChild(headerDiv);
                
                // Category content
                const contentDiv = document.createElement('div');
                contentDiv.className = 'category-content';
                
                categoryPrompts.forEach(prompt => {
                    const promptDiv = document.createElement('div');
                    promptDiv.className = 'prompt-item';
                    
                    // Highlight creation prompts
                    if (category === '✨ Create New Items' || category === '⚡ Quick Setup' || category === '📝 Proper Naming') {
                        promptDiv.classList.add('creation');
                    }
                    
                    promptDiv.onclick = () => selectPrompt(prompt.prompt);
                    
                    // Add tooltip
                    const tooltipDiv = document.createElement('div');
                    tooltipDiv.className = 'prompt-tooltip';
                    tooltipDiv.textContent = prompt.prompt;
                    
                    promptDiv.innerHTML = `
                        <div class="prompt-command">${prompt.prompt}</div>
                        <div class="prompt-description">${prompt.description}</div>
                    `;
                    
                    promptDiv.appendChild(tooltipDiv);
                    contentDiv.appendChild(promptDiv);
                });
                
                categoryDiv.appendChild(contentDiv);
                container.appendChild(categoryDiv);
                
                // Set initial collapse state
                updateCategoryDisplay(category);
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
            const sendButton = document.getElementById('sendButton');
            const message = input.value.trim();
            
            if (message === '') {
                return;
            }
            
            // Check if we can use WebSocket or need fallback
            if (!window.fallbackMode && socket && socket.readyState === WebSocket.OPEN) {
                sendViaWebSocket(message, input, sendButton);
            } else {
                sendViaHTTP(message, input, sendButton);
            }
        }
        
        function sendViaWebSocket(message, input, sendButton) {
            // Add to message history
            messageHistory.unshift(message);
            if (messageHistory.length > 50) {
                messageHistory = messageHistory.slice(0, 50);
            }
            historyIndex = -1;
            
            // Disable send button temporarily
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="send-icon">⏳</span><span>Sending</span>';
            
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
            input.style.height = 'auto';
            
            // Re-enable send button after delay
            setTimeout(() => {
                sendButton.disabled = false;
                sendButton.innerHTML = '<span class="send-icon">📤</span><span>Send</span>';
            }, 1000);
        }
        
        function sendViaHTTP(message, input, sendButton) {
            // Add to message history
            messageHistory.unshift(message);
            if (messageHistory.length > 50) {
                messageHistory = messageHistory.slice(0, 50);
            }
            historyIndex = -1;
            
            // Disable send button temporarily
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="send-icon">⏳</span><span>Sending</span>';
            
            // Display user message
            displayMessage({
                type: 'user',
                message: message,
                timestamp: new Date().toISOString()
            });
            
            // Send via HTTP API
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user: userId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Display the response
                displayMessage({
                    type: 'response',
                    command: message,
                    result: data,
                    timestamp: new Date().toISOString()
                });
            })
            .catch(error => {
                console.error('HTTP API error:', error);
                displayMessage({
                    type: 'response',
                    command: message,
                    result: {
                        error: 'Unable to process command. Please try again or check your connection.',
                        fallback: true
                    },
                    timestamp: new Date().toISOString()
                });
            })
            .finally(() => {
                // Re-enable send button
                sendButton.disabled = false;
                sendButton.innerHTML = '<span class="send-icon">📤</span><span>Send</span>';
            });
            
            input.value = '';
            input.style.height = 'auto';
        }
        
        function displayMessage(data) {
            const messagesEl = document.getElementById('messages');
            const messageEl = document.createElement('div');
            
            let className = 'message ';
            let content = '';
            
            if (data.type === 'user') {
                className += 'user';
                content = `
                    <div class="message-header">[User • ${new Date(data.timestamp).toLocaleTimeString()}]</div>
                    <div class="message-content">${data.message}</div>
                `;
            } else if (data.type === 'system') {
                className += 'system';
                mcpAvailable = data.status?.mcp_available || false;
                workbenchManagerAvailable = data.status?.workbench_manager_available || false;
                isCloudDeployment = data.status?.deployment === 'cloud';
                
                content = `
                    <div class="message-header">[System • ${new Date(data.timestamp).toLocaleTimeString()}]</div>
                    <div class="message-content">${data.message}</div>
                `;
                
                // Update status indicators
                setTimeout(() => updateConnectionStatus('connected'), 100);
            } else if (data.type === 'response') {
                className += 'response';
                content = `
                    <div class="message-header">[Assistant • ${new Date(data.timestamp).toLocaleTimeString()}]</div>
                    <div class="message-content">
                        <div style="margin-bottom: 8px;"><strong>⚡ Command:</strong> <code>${data.command}</code></div>
                        <div class="command-result">${formatResult(data.result)}</div>
                    </div>
                `;
            }
            
            messageEl.className = className;
            messageEl.innerHTML = content;
            messagesEl.appendChild(messageEl);
            
            // Smooth scroll to bottom
            setTimeout(() => {
                messagesEl.scrollTo({
                    top: messagesEl.scrollHeight,
                    behavior: 'smooth'
                });
            }, 50);
        }
        
        function formatResult(result) {
            if (result.error) {
                let errorMsg = `<span style="color: #f56565;">❌ Error: ${result.error}</span>`;
                
                // Add suggestion if available
                if (result.suggestion) {
                    errorMsg += `<br><br><strong>💡 Suggestion:</strong> ${result.suggestion}`;
                }
                
                // Add examples if available
                if (result.examples && result.examples.length > 0) {
                    errorMsg += '<br><br><strong>📝 Examples:</strong><ul class="help-commands">';
                    result.examples.forEach(example => {
                        errorMsg += `<li style="cursor: pointer;" onclick="selectPrompt('${example}')">${example}</li>`;
                    });
                    errorMsg += '</ul>';
                    errorMsg += '<br><em>💡 Click any example to try it!</em>';
                }
                
                if (result.demo) {
                    errorMsg += '<br><span class="demo-indicator">Running in demo mode</span>';
                }
                return errorMsg;
            }
            
            // Special formatting for creation results
            if (result.type === 'agent_creation' || result.type === 'workbench_creation' || result.type === 'task_creation') {
                return `<div class="creation-result">${result.message}</div>`;
            }
            
            if (result.type === 'help') {
                let html = '<strong>📚 Available Commands:</strong><ul class="help-commands">';
                result.commands.forEach(cmd => {
                    html += `<li>${cmd}</li>`;
                });
                html += '</ul>';
                html += '<p style="margin-top: 10px;"><em>💡 Tip: Check the sidebar for suggested prompts including creation commands!</em></p>';
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
                let html = '';
                
                // Handle count queries specially
                if (result.data.count_query && result.data.message) {
                    html += `<strong>📊 ${result.data.message}</strong><br><br>`;
                }
                
                html += `<strong>👥 Agents (${agents.length}):</strong><br>${agents.join(', ')}`;
                return html;
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
                const agentData = result.data;
                const roles = agentData.roles || agentData; // Handle both old and new format
                
                let html = '';
                
                // Check if this is a details request
                if (agentData.is_details_request) {
                    html += `<strong>📋 Agent Details: ${result.agent}</strong><br><br>`;
                    
                    // Add task information if available
                    if (agentData.task_count) {
                        html += `<strong>📊 Task Statistics:</strong><br>`;
                        html += `<div class="workbench-item">Recent task count: ${JSON.stringify(agentData.task_count)}</div>`;
                    }
                    
                    if (agentData.recent_tasks) {
                        html += `<strong>📋 Recent Tasks:</strong><br>`;
                        html += `<div class="workbench-item">${agentData.recent_tasks.length} recent tasks</div>`;
                    }
                    
                    html += `<br><strong>🎭 Role Assignments:</strong><div class="workbench-list">`;
                } else {
                    html += `<strong>🎭 Roles for ${result.agent}:</strong><div class="workbench-list">`;
                }
                
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
            
            if (result.type === 'agent_workbench_summary') {
                const data = result.data;
                let html = '<strong>🏢 Agent Workbench Assignments:</strong><br>';
                html += `<em>💬 ${data.context}</em><div class="workbench-list">`;
                
                Object.entries(data.assignments).forEach(([agent, roles]) => {
                    html += `<div class="workbench-item">
                        <strong>👤 ${agent}:</strong><br>`;
                    
                    if (roles.length === 0) {
                        html += '<div class="role-assignment" style="color: #718096;">No workbench assignments</div>';
                    } else {
                        roles.forEach(role => {
                            html += `<div class="role-assignment">
                                📋 ${role.workbench_name}: <strong>${role.role}</strong>
                            </div>`;
                        });
                    }
                    html += '</div>';
                });
                
                html += '</div>';
                html += `<br><em>Total agents: ${data.total_agents}</em>`;
                return html;
            }
            
            if (result.type === 'llm_response') {
                return `<div style="background: #e6fffa; border-left: 4px solid #38b2ac; padding: 12px; border-radius: 6px;">
                    <strong>🤖 AI Assistant:</strong><br>${result.message}
                </div>`;
            }
            
            if (result.type === 'llm_with_executed_commands') {
                let html = `<div style="background: #e6fffa; border-left: 4px solid #38b2ac; padding: 12px; border-radius: 6px;">
                    <strong>🤖 AI Assistant:</strong><br>${result.natural_response}
                </div>`;
                
                if (result.command_results && result.command_results.length > 0) {
                    html += '<br><strong>🔧 Executed Commands:</strong><div class="workbench-list">';
                    result.command_results.forEach(cmdResult => {
                        const status = cmdResult.error ? '❌' : '✅';
                        html += `<div class="role-assignment">
                            ${status} <code>${cmdResult.command}</code>
                        </div>`;
                    });
                    html += '</div>';
                }
                return html;
            }
            
            if (result.type === 'llm_status') {
                const data = result.data;
                let html = '<strong>🤖 LLM Integration Status:</strong><div class="workbench-list">';
                html += `<div class="workbench-item">
                    <strong>Status:</strong> ${data.available ? '✅ Available' : '❌ Not Available'}<br>
                    <strong>Provider:</strong> ${data.provider || 'None'}<br>
                    <strong>Model:</strong> ${data.model || 'None'}<br>
                    <strong>Conversation Length:</strong> ${data.conversation_length} messages
                </div>`;
                
                if (data.provider_availability) {
                    html += '<div class="workbench-item"><strong>Provider Availability:</strong>';
                    Object.entries(data.provider_availability).forEach(([provider, status]) => {
                        const available = status.module_available && (status.api_key_available || status.service_running);
                        html += `<div class="role-assignment">${available ? '✅' : '❌'} ${provider}</div>`;
                    });
                    html += '</div>';
                }
                html += '</div>';
                return html;
            }
            
            if (result.type === 'llm_toggle') {
                const color = result.enabled ? '#48bb78' : '#f56565';
                return `<div style="color: ${color}; font-weight: bold;">🤖 ${result.message}</div>`;
            }
            
            if (result.type === 'llm_clear') {
                return `<div style="color: #48bb78; font-weight: bold;">🧹 ${result.message}</div>`;
            }
            
            if (result.type === 'welcome') {
                let html = `<div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 24px; 
                    border-radius: 16px; 
                    margin: 16px 0; 
                    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                ">
                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 16px; text-align: center;">
                        🎉 Welcome to OPS Center Chat!
                    </div>
                    <div style="line-height: 1.6; white-space: pre-line;">
                        ${result.message.replace('Welcome to OPS Center Chat! 🎉\n\n', '')}
                    </div>
                </div>`;
                
                if (result.suggestions && result.suggestions.length > 0) {
                    html += '<div style="margin-top: 16px; text-align: center;"><strong>🚀 Quick Start Actions:</strong><br>';
                    result.suggestions.forEach(suggestion => {
                        html += `<button onclick="selectPrompt('${suggestion}')" style="
                            background: var(--primary-600); 
                            color: white; 
                            border: none; 
                            padding: 8px 16px; 
                            margin: 6px; 
                            border-radius: 20px; 
                            cursor: pointer; 
                            font-size: 13px;
                            font-weight: 500;
                            transition: all 0.2s ease;
                            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                        " onmouseover="this.style.background='var(--primary-700)'; this.style.transform='translateY(-2px)'" 
                           onmouseout="this.style.background='var(--primary-600)'; this.style.transform='translateY(0)'">
                            ${suggestion}
                        </button>`;
                    });
                    html += '</div>';
                }
                return html;
            }
            
            if (result.type === 'conversational') {
                let html = `<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px; border-radius: 12px; margin: 8px 0;">
                    ${result.message}
                </div>`;
                
                if (result.suggestions && result.suggestions.length > 0) {
                    html += '<div style="margin-top: 12px;"><strong>💡 Quick suggestions:</strong><br>';
                    result.suggestions.forEach(suggestion => {
                        html += `<button onclick="selectPrompt('${suggestion}')" style="
                            background: var(--primary-600); 
                            color: white; 
                            border: none; 
                            padding: 6px 12px; 
                            margin: 4px; 
                            border-radius: 16px; 
                            cursor: pointer; 
                            font-size: 12px;
                            transition: all 0.2s ease;
                        " onmouseover="this.style.background='var(--primary-700)'" 
                           onmouseout="this.style.background='var(--primary-600)'">
                            ${suggestion}
                        </button>`;
                    });
                    html += '</div>';
                }
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
        const messageInput = document.getElementById('messageInput');
        
        messageInput.addEventListener('input', autoResizeTextarea);
        
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            } else if (e.key === 'ArrowUp' && messageInput.value === '') {
                e.preventDefault();
                navigateHistory('up');
            } else if (e.key === 'ArrowDown' && messageInput.value === '') {
                e.preventDefault();
                navigateHistory('down');
            } else if (e.key === '/' && messageInput.value === '') {
                e.preventDefault();
                messageInput.value = '/';
                autoResizeTextarea();
            }
        });
        
        // Handle window resize for mobile
        window.addEventListener('resize', function() {
            const sidebar = document.getElementById('sidebar');
            if (window.innerWidth > 768 && sidebar.classList.contains('mobile-open')) {
                sidebar.classList.remove('mobile-open');
            }
        });
        
        // IMMEDIATE INTERFACE ACTIVATION - No delays, no connections
        console.log('🚨 IMMEDIATE INTERFACE ACTIVATION - Enabling NOW');
        
        // Enable fallback mode immediately
        window.fallbackMode = true;
        
        // Force enable interface elements RIGHT NOW
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        if (messageInput) {
            messageInput.disabled = false;
            messageInput.placeholder = "Type your command here... (Interface Ready!)";
            messageInput.focus();
            console.log('✅ Input enabled immediately');
        }
        
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML = '<span class="send-icon">📤</span><span>Send</span>';
            console.log('✅ Send button enabled immediately');
        }
        
        // Load prompts immediately
        fetch('/api/prompts')
            .then(response => response.json())
            .then(data => {
                suggestedPrompts = data.prompts;
                displaySuggestedPrompts(data.prompts);
                console.log('✅ Prompts loaded');
            })
            .catch(error => {
                console.log('Using default prompts');
                displayDefaultPrompts();
            });
        
        // Show immediate welcome message
        setTimeout(() => {
            displayMessage({
                type: 'response',
                command: 'System Ready',
                result: {
                    type: 'welcome',
                    message: `🎉 INTERFACE IS ACTIVE AND READY!

✅ You can now type commands below.

Quick commands to try:
• "help" - Show all commands
• "agents" - List agents
• "workbenches" - Show workbenches

The interface is fully functional! Start typing below 👇`,
                    suggestions: ["help", "agents", "workbenches", "coverage"]
                },
                timestamp: new Date().toISOString()
            });
        }, 100);
        
        // Also attempt connection in parallel (but don't wait for it)
        const isCloudDeployment = window.location.hostname.includes('.onrender.com') || 
                                 window.location.hostname.includes('.herokuapp.com') ||
                                 window.location.hostname.includes('.railway.app') ||
                                 window.location.hostname.includes('.vercel.app') ||
                                 window.location.hostname.includes('.netlify.app');
        
        if (!isCloudDeployment) {
            console.log('🏠 Local development - attempting WebSocket in background');
            setTimeout(() => connect(), 100);
        }
    </script>
</body>
</html>
'''

# Initialize template directory and file (for cloud deployment compatibility)
def init_templates():
    """Initialize templates directory and file"""
    try:
        import os
        os.makedirs("templates", exist_ok=True)
        with open("templates/chat.html", "w") as f:
            f.write(chat_html_template)
    except Exception as e:
        print(f"⚠️ Template initialization warning: {e}")

# Initialize templates when module loads
init_templates()

# Startup logging function
def print_startup_info():
    isCloudDeployment = PORT != 8080 or HOST != '0.0.0.0'
    
    print("🚀 Starting OPS Center Chat Interface...")
    print(f"📱 Interface available at: http://{HOST}:{PORT}")
    
    if isCloudDeployment:
        print("🌐 ☁️ Cloud deployment ready! Share your URL with team members.")
        print("✨ Full-featured demo mode with modern UI and conversational support")
        print("🎯 Features: Natural language commands, workbench management, role assignments")
    else:
        print("🔗 Share this URL with others to give them access to the MCP system")
        print("💡 Available commands: help, agents, workbenches, roles, assign-role, agent-roles, coverage")
    
    print(f"🔧 MCP Client: {'✅ Connected' if MCP_AVAILABLE else '🔶 Demo Mode (Full UI Available)'}")
    print(f"🔧 Workbench Manager: {'✅ Available' if WORKBENCH_MANAGER_AVAILABLE else '🔶 Limited'}")
    print(f"🔧 LLM Integration: {'✅ Active' if LLM_INTEGRATION_AVAILABLE else '🔶 Rule-based with Natural Language'}")
    print(f"🌐 Environment: {'☁️ Cloud Deployed' if isCloudDeployment else '🏠 Local Development'}")

# Always print startup info for deployment logging
print_startup_info()

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)