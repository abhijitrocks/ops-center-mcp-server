#!/usr/bin/env python3
"""
MCP Client for OPS Center
A client to interact with the MCP server via JSON-RPC
"""

import json
import requests
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MCPClientConfig:
    """Configuration for MCP Client"""
    server_url: str = "http://localhost:8000"
    rpc_endpoint: str = "/rpc"
    timeout: int = 30


class MCPClient:
    """MCP Client for interacting with the OPS Center MCP Server"""
    
    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self.base_url = self.config.server_url
        self.rpc_url = f"{self.base_url}{self.config.rpc_endpoint}"
        self._request_id = 0
        
    def _get_next_id(self) -> int:
        """Get next request ID"""
        self._request_id += 1
        return self._request_id
    
    def _create_rpc_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Create a JSON-RPC 2.0 request"""
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._get_next_id()
        }
    
    def _handle_rpc_response(self, response: Dict) -> Any:
        """Handle JSON-RPC response and extract result or raise error"""
        if "error" in response and response["error"] is not None:
            error = response["error"]
            raise Exception(f"RPC Error {error.get('code', 'Unknown')}: {error.get('message', 'Unknown error')}")
        return response.get("result")

    async def _async_rpc_call(self, method: str, params: Optional[Dict] = None) -> Any:
        """Make an async JSON-RPC call"""
        request_data = self._create_rpc_request(method, params)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
            async with session.post(self.rpc_url, json=request_data) as response:
                response.raise_for_status()
                result = await response.json()
                return self._handle_rpc_response(result)
    
    def _sync_rpc_call(self, method: str, params: Optional[Dict] = None) -> Any:
        """Make a synchronous JSON-RPC call"""
        request_data = self._create_rpc_request(method, params)
        
        response = requests.post(
            self.rpc_url, 
            json=request_data, 
            timeout=self.config.timeout
        )
        response.raise_for_status()
        result = response.json()
        return self._handle_rpc_response(result)

    # Synchronous methods
    def get_agent_task_count(self, agent: str, days: int = 3) -> Dict:
        """Get the number of completed tasks for an agent in the last N days"""
        return self._sync_rpc_call("get_agent_task_count", {"agent": agent, "days": days})
    
    def list_recent_tasks(self, agent: str, limit: int = 5) -> List[Dict]:
        """List recent completed tasks for an agent"""
        return self._sync_rpc_call("list_recent_tasks", {"agent": agent, "limit": limit})
    
    def average_completion_time(self, agent: str) -> Dict:
        """Get average completion time for an agent"""
        return self._sync_rpc_call("average_completion_time", {"agent": agent})
    
    def list_tags(self, tenant_id: int) -> List[Dict]:
        """List all tags for a tenant"""
        return self._sync_rpc_call("list_tags", {"tenant_id": tenant_id})
    
    def assign_task(self, agent: str, task_id: int, workbench_id: Optional[int] = None) -> Dict:
        """Assign a task to an agent"""
        params = {"agent": agent, "task_id": task_id}
        if workbench_id is not None:
            params["workbench_id"] = workbench_id
        return self._sync_rpc_call("assign_task", params)
    
    def update_task_status(self, task_id: int, agent: Optional[str] = None, status: str = "completed") -> Dict:
        """Update task status"""
        params = {"task_id": task_id, "status": status}
        if agent is not None:
            params["agent"] = agent
        return self._sync_rpc_call("update_task_status", params)
    
    def list_agents(self, limit: int = 100) -> Dict:
        """List all agents in the system"""
        return self._sync_rpc_call("list_agents", {"limit": limit})
    
    def get_agent_info(self, agent: str) -> Dict:
        """Get detailed information about a specific agent"""
        return self._sync_rpc_call("get_agent_info", {"agent": agent})
    
    def get_agent_stats(self, days: int = 7) -> Dict:
        """Get statistics for all agents in the last N days"""
        return self._sync_rpc_call("get_agent_stats", {"days": days})
    
    # Async methods
    async def async_get_agent_task_count(self, agent: str, days: int = 3) -> Dict:
        """Async version of get_agent_task_count"""
        return await self._async_rpc_call("get_agent_task_count", {"agent": agent, "days": days})
    
    async def async_list_recent_tasks(self, agent: str, limit: int = 5) -> List[Dict]:
        """Async version of list_recent_tasks"""
        return await self._async_rpc_call("list_recent_tasks", {"agent": agent, "limit": limit})
    
    async def async_average_completion_time(self, agent: str) -> Dict:
        """Async version of average_completion_time"""
        return await self._async_rpc_call("average_completion_time", {"agent": agent})
    
    async def async_list_tags(self, tenant_id: int) -> List[Dict]:
        """Async version of list_tags"""
        return await self._async_rpc_call("list_tags", {"tenant_id": tenant_id})
    
    async def async_assign_task(self, agent: str, task_id: int, workbench_id: Optional[int] = None) -> Dict:
        """Async version of assign_task"""
        params = {"agent": agent, "task_id": task_id}
        if workbench_id is not None:
            params["workbench_id"] = workbench_id
        return await self._async_rpc_call("assign_task", params)
    
    async def async_update_task_status(self, task_id: int, agent: Optional[str] = None, status: str = "completed") -> Dict:
        """Async version of update_task_status"""
        params = {"task_id": task_id, "status": status}
        if agent is not None:
            params["agent"] = agent
        return await self._async_rpc_call("update_task_status", params)
    
    async def async_list_agents(self, limit: int = 100) -> Dict:
        """Async version of list_agents"""
        return await self._async_rpc_call("list_agents", {"limit": limit})
    
    async def async_get_agent_info(self, agent: str) -> Dict:
        """Async version of get_agent_info"""
        return await self._async_rpc_call("get_agent_info", {"agent": agent})
    
    async def async_get_agent_stats(self, days: int = 7) -> Dict:
        """Async version of get_agent_stats"""
        return await self._async_rpc_call("get_agent_stats", {"days": days})

    # Health check and utility methods
    def health_check(self) -> Dict:
        """Check if the server is healthy"""
        try:
            # Try the /health endpoint first
            response = requests.get(f"{self.base_url}/health", timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except:
            # Fallback to RPC method to test connectivity
            try:
                result = self._sync_rpc_call("get_agent_task_count", {"agent": "health_check", "days": 1})
                return {"status": "OK", "rpc_working": True}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
    
    async def async_health_check(self) -> Dict:
        """Async health check"""
        try:
            # Try the /health endpoint first
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    response.raise_for_status()
                    return await response.json()
        except:
            # Fallback to RPC method to test connectivity
            try:
                result = await self._async_rpc_call("get_agent_task_count", {"agent": "health_check", "days": 1})
                return {"status": "OK", "rpc_working": True}
            except Exception as e:
                return {"status": "ERROR", "error": str(e)}

    def get_server_info(self) -> Dict:
        """Get server information from OpenAPI spec"""
        response = requests.get(f"{self.base_url}/openapi.json", timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()


# Example usage and CLI functionality
def main():
    """Example usage of the MCP Client"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Client for OPS Center")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--agent", required=True, help="Agent name")
    parser.add_argument("--action", choices=[
        "health", "task_count", "recent_tasks", "avg_time", "assign", "update_status",
        "list_agents", "agent_info", "agent_stats"
    ], required=True, help="Action to perform")
    parser.add_argument("--task-id", type=int, help="Task ID (for assign/update)")
    parser.add_argument("--status", default="completed", help="Status (for update)")
    parser.add_argument("--days", type=int, default=3, help="Days for task count")
    parser.add_argument("--limit", type=int, default=5, help="Limit for recent tasks")
    parser.add_argument("--tenant-id", type=int, help="Tenant ID (for tags)")
    
    args = parser.parse_args()
    
    config = MCPClientConfig(server_url=args.server)
    client = MCPClient(config)
    
    try:
        if args.action == "health":
            result = client.health_check()
            print("Server Health:", json.dumps(result, indent=2))
            
        elif args.action == "task_count":
            result = client.get_agent_task_count(args.agent, args.days)
            print("Task Count:", json.dumps(result, indent=2))
            
        elif args.action == "recent_tasks":
            result = client.list_recent_tasks(args.agent, args.limit)
            print("Recent Tasks:", json.dumps(result, indent=2))
            
        elif args.action == "avg_time":
            result = client.average_completion_time(args.agent)
            print("Average Completion Time:", json.dumps(result, indent=2))
            
        elif args.action == "assign":
            if not args.task_id:
                print("Error: --task-id is required for assign action")
                return
            result = client.assign_task(args.agent, args.task_id)
            print("Task Assigned:", json.dumps(result, indent=2))
            
        elif args.action == "update_status":
            if not args.task_id:
                print("Error: --task-id is required for update_status action")
                return
            result = client.update_task_status(args.task_id, args.agent, args.status)
            print("Task Status Updated:", json.dumps(result, indent=2))
            
        elif args.action == "list_agents":
            result = client.list_agents(limit=args.limit if hasattr(args, 'limit') else 100)
            print("Agents List:", json.dumps(result, indent=2))
            
        elif args.action == "agent_info":
            result = client.get_agent_info(args.agent)
            print("Agent Info:", json.dumps(result, indent=2))
            
        elif args.action == "agent_stats":
            result = client.get_agent_stats(days=args.days)
            print("Agent Statistics:", json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()