#!/usr/bin/env python3
"""
Example usage of the MCP Client for OPS Center
This script demonstrates both synchronous and asynchronous operations
"""

import asyncio
import json
from mcp_client import MCPClient, MCPClientConfig


def sync_example():
    """Example of synchronous client usage"""
    print("=== Synchronous MCP Client Example ===")
    
    # Initialize client with default configuration (localhost:8000)
    client = MCPClient()
    
    # Or initialize with custom configuration
    # config = MCPClientConfig(
    #     server_url="https://your-mcp-server.com",
    #     timeout=60
    # )
    # client = MCPClient(config)
    
    try:
        # Health check
        print("1. Health Check:")
        health = client.health_check()
        print(f"   Server Status: {health}")
        
        # Get agent task count
        print("\n2. Agent Task Count:")
        task_count = client.get_agent_task_count("agent_1", days=7)
        print(f"   {task_count}")
        
        # List recent tasks
        print("\n3. Recent Tasks:")
        recent_tasks = client.list_recent_tasks("agent_1", limit=3)
        print(f"   Found {len(recent_tasks)} recent tasks")
        for task in recent_tasks:
            print(f"   - Task ID: {task.get('task_id')}, Status: {task.get('status')}")
        
        # Get average completion time
        print("\n4. Average Completion Time:")
        avg_time = client.average_completion_time("agent_1")
        print(f"   {avg_time}")
        
        # Assign a new task
        print("\n5. Assign New Task:")
        new_task = client.assign_task("agent_1", task_id=1001)
        print(f"   Task assigned: {new_task}")
        
        # Update task status
        print("\n6. Update Task Status:")
        updated_task = client.update_task_status(1001, agent="agent_1", status="in_progress")
        print(f"   Task updated: {updated_task}")
        
        # List tags (requires tenant_id)
        print("\n7. List Tags:")
        try:
            tags = client.list_tags(tenant_id=1)
            print(f"   Found {len(tags)} tags")
            for tag in tags:
                print(f"   - {tag.get('name')}: {tag.get('description', 'No description')}")
        except Exception as e:
            print(f"   Error listing tags: {e}")
            
    except Exception as e:
        print(f"Error in sync example: {e}")


async def async_example():
    """Example of asynchronous client usage"""
    print("\n=== Asynchronous MCP Client Example ===")
    
    # Initialize client
    client = MCPClient()
    
    try:
        # Health check
        print("1. Async Health Check:")
        health = await client.async_health_check()
        print(f"   Server Status: {health}")
        
        # Run multiple operations concurrently
        print("\n2. Concurrent Operations:")
        agent_name = "agent_2"
        
        # Execute multiple async operations concurrently
        results = await asyncio.gather(
            client.async_get_agent_task_count(agent_name, days=30),
            client.async_list_recent_tasks(agent_name, limit=5),
            client.async_average_completion_time(agent_name),
            return_exceptions=True
        )
        
        task_count, recent_tasks, avg_time = results
        
        if not isinstance(task_count, Exception):
            print(f"   Task Count: {task_count}")
        
        if not isinstance(recent_tasks, Exception):
            print(f"   Recent Tasks: {len(recent_tasks)} found")
            
        if not isinstance(avg_time, Exception):
            print(f"   Average Time: {avg_time}")
        
        # Assign multiple tasks concurrently
        print("\n3. Assign Multiple Tasks Concurrently:")
        task_assignments = await asyncio.gather(
            client.async_assign_task(agent_name, 2001),
            client.async_assign_task(agent_name, 2002),
            client.async_assign_task(agent_name, 2003),
            return_exceptions=True
        )
        
        for i, assignment in enumerate(task_assignments, 2001):
            if not isinstance(assignment, Exception):
                print(f"   Task {i} assigned successfully")
            else:
                print(f"   Task {i} assignment failed: {assignment}")
        
    except Exception as e:
        print(f"Error in async example: {e}")


def workflow_example():
    """Example of a complete workflow using the MCP client"""
    print("\n=== Workflow Example ===")
    
    client = MCPClient()
    agent_name = "workflow_agent"
    
    try:
        print("1. Starting workflow...")
        
        # Step 1: Check server health
        health = client.health_check()
        if health.get("status") != "OK":
            print("   Server is not healthy, aborting workflow")
            return
        
        # Step 2: Get current agent stats
        print("2. Getting current agent statistics...")
        task_count = client.get_agent_task_count(agent_name, days=1)
        print(f"   Agent has completed {task_count.get('completed_tasks', 0)} tasks today")
        
        # Step 3: Assign a batch of tasks
        print("3. Assigning batch of tasks...")
        task_ids = [3001, 3002, 3003, 3004, 3005]
        assigned_tasks = []
        
        for task_id in task_ids:
            try:
                assigned = client.assign_task(agent_name, task_id)
                assigned_tasks.append(assigned)
                print(f"   ✓ Task {task_id} assigned")
            except Exception as e:
                print(f"   ✗ Task {task_id} failed: {e}")
        
        # Step 4: Simulate task completion
        print("4. Simulating task completion...")
        for task in assigned_tasks[:3]:  # Complete first 3 tasks
            try:
                task_id = task.get('task_id')
                client.update_task_status(task_id, agent=agent_name, status="completed")
                print(f"   ✓ Task {task_id} completed")
            except Exception as e:
                print(f"   ✗ Task {task_id} completion failed: {e}")
        
        # Step 5: Get updated stats
        print("5. Getting updated statistics...")
        new_task_count = client.get_agent_task_count(agent_name, days=1)
        recent_tasks = client.list_recent_tasks(agent_name, limit=10)
        
        print(f"   Agent now has completed {new_task_count.get('completed_tasks', 0)} tasks today")
        print(f"   Recent tasks: {len(recent_tasks)} found")
        
        print("6. Workflow completed successfully!")
        
    except Exception as e:
        print(f"Workflow failed: {e}")


def interactive_mode():
    """Interactive mode for testing the MCP client"""
    print("\n=== Interactive Mode ===")
    print("Commands: health, count <agent>, recent <agent>, assign <agent> <task_id>, quit")
    
    client = MCPClient()
    
    while True:
        try:
            command = input("\n> ").strip().split()
            if not command:
                continue
                
            if command[0] == "quit":
                break
            elif command[0] == "health":
                result = client.health_check()
                print(f"Health: {result}")
            elif command[0] == "count" and len(command) > 1:
                agent = command[1]
                result = client.get_agent_task_count(agent)
                print(f"Task count for {agent}: {result}")
            elif command[0] == "recent" and len(command) > 1:
                agent = command[1]
                result = client.list_recent_tasks(agent, limit=5)
                print(f"Recent tasks for {agent}: {len(result)} found")
                for task in result:
                    print(f"  - {task}")
            elif command[0] == "assign" and len(command) > 2:
                agent = command[1]
                task_id = int(command[2])
                result = client.assign_task(agent, task_id)
                print(f"Task assigned: {result}")
            else:
                print("Unknown command or missing arguments")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")


def main():
    """Main function to run examples"""
    print("MCP Client Examples for OPS Center")
    print("=" * 50)
    
    # Run synchronous example
    sync_example()
    
    # Run asynchronous example
    asyncio.run(async_example())
    
    # Run workflow example
    workflow_example()
    
    # Uncomment to run interactive mode
    # interactive_mode()


if __name__ == "__main__":
    main()