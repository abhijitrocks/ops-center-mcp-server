#!/usr/bin/env python3
"""
Async example of using MCP Client
"""

import asyncio
from mcp_client import MCPClient, MCPClientConfig

async def main():
    # Initialize client
    config = MCPClientConfig(
        server_url="http://localhost:8000",
        timeout=30
    )
    client = MCPClient(config)
    
    try:
        # Async health check
        print("=== Async Health Check ===")
        health = await client.async_health_check()
        print(f"Server status: {health}")
        
        # Run multiple operations concurrently
        print("\n=== Concurrent Operations ===")
        agent_name = "my_agent"
        
        # Execute multiple operations at the same time
        results = await asyncio.gather(
            client.async_get_agent_task_count(agent_name, days=7),
            client.async_list_recent_tasks(agent_name, limit=3),
            client.async_average_completion_time(agent_name),
            return_exceptions=True  # Don't fail if one operation fails
        )
        
        task_count, recent_tasks, avg_time = results
        
        if not isinstance(task_count, Exception):
            print(f"Task count: {task_count}")
        else:
            print(f"Task count error: {task_count}")
            
        if not isinstance(recent_tasks, Exception):
            print(f"Recent tasks: {recent_tasks}")
        else:
            print(f"Recent tasks error: {recent_tasks}")
            
        if not isinstance(avg_time, Exception):
            print(f"Average time: {avg_time}")
        else:
            print(f"Average time error: {avg_time}")
        
        # Assign multiple tasks concurrently
        print("\n=== Concurrent Task Assignment ===")
        task_assignments = await asyncio.gather(
            client.async_assign_task(agent_name, 2001),
            client.async_assign_task(agent_name, 2002),
            client.async_assign_task(agent_name, 2003),
            return_exceptions=True
        )
        
        for i, assignment in enumerate(task_assignments, 2001):
            if not isinstance(assignment, Exception):
                print(f"Task {i} assigned: {assignment}")
            else:
                print(f"Task {i} assignment failed: {assignment}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())