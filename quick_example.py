#!/usr/bin/env python3
"""
Quick example of using MCP Client in Python
"""

from mcp_client import MCPClient, MCPClientConfig

# Method 1: Use default configuration (localhost:8000)
client = MCPClient()

# Method 2: Use custom configuration
config = MCPClientConfig(
    server_url="https://your-server.com",
    timeout=60
)
client = MCPClient(config)

try:
    # Health check
    print("=== Health Check ===")
    health = client.health_check()
    print(f"Server status: {health}")
    
    # Get agent task count
    print("\n=== Agent Task Count ===")
    task_count = client.get_agent_task_count("my_agent", days=7)
    print(f"Task count: {task_count}")
    
    # List recent tasks
    print("\n=== Recent Tasks ===")
    tasks = client.list_recent_tasks("my_agent", limit=5)
    print(f"Recent tasks: {tasks}")
    
    # Get average completion time
    print("\n=== Average Completion Time ===")
    avg_time = client.average_completion_time("my_agent")
    print(f"Average time: {avg_time}")
    
    # Assign a task
    print("\n=== Assign Task ===")
    new_task = client.assign_task("my_agent", task_id=1234)
    print(f"Assigned task: {new_task}")
    
    # Update task status
    print("\n=== Update Task Status ===")
    updated_task = client.update_task_status(1234, agent="my_agent", status="in_progress")
    print(f"Updated task: {updated_task}")
    
    # Complete the task
    completed_task = client.update_task_status(1234, agent="my_agent", status="completed")
    print(f"Completed task: {completed_task}")
    
    # List tags (if you have tenant_id)
    print("\n=== List Tags ===")
    try:
        tags = client.list_tags(tenant_id=1)
        print(f"Tags: {tags}")
    except Exception as e:
        print(f"Tags error (expected if no tenant): {e}")

except Exception as e:
    print(f"Error: {e}")