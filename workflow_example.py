#!/usr/bin/env python3
"""
Complete workflow example using MCP Client
This shows a real-world scenario of managing tasks with an agent
"""

from mcp_client import MCPClient, MCPClientConfig
import time

def agent_workflow():
    """Complete workflow for managing agent tasks"""
    
    # Initialize client with your server
    config = MCPClientConfig(
        server_url="http://localhost:8000",  # Change to your server URL
        timeout=30
    )
    client = MCPClient(config)
    
    agent_name = "workflow_agent"
    
    print("🚀 Starting Agent Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Health check
        print("1️⃣ Checking server health...")
        health = client.health_check()
        print(f"   ✅ Server status: {health.get('status', 'Unknown')}")
        
        # Step 2: Get current agent statistics
        print("\n2️⃣ Getting current agent statistics...")
        try:
            task_count = client.get_agent_task_count(agent_name, days=1)
            print(f"   📊 Tasks completed today: {task_count.get('completed_tasks', 0)}")
            
            avg_time = client.average_completion_time(agent_name)
            avg_seconds = avg_time.get('average_completion_time_seconds', 0)
            print(f"   ⏱️  Average completion time: {avg_seconds:.2f} seconds")
        except Exception as e:
            print(f"   ⚠️  Statistics unavailable: {e}")
        
        # Step 3: Assign new tasks
        print("\n3️⃣ Assigning new tasks...")
        task_ids = [5001, 5002, 5003]
        assigned_tasks = []
        
        for task_id in task_ids:
            try:
                task = client.assign_task(agent_name, task_id)
                assigned_tasks.append(task)
                print(f"   ✅ Task {task_id} assigned successfully")
            except Exception as e:
                print(f"   ❌ Task {task_id} assignment failed: {e}")
        
        # Step 4: Update task statuses (simulate work)
        print("\n4️⃣ Processing tasks...")
        for i, task in enumerate(assigned_tasks):
            task_id = task.get('task_id')
            
            # Start task
            try:
                client.update_task_status(task_id, agent=agent_name, status="in_progress")
                print(f"   🔄 Task {task_id} started")
                
                # Simulate work (you'd do real work here)
                time.sleep(1)
                
                # Complete task
                client.update_task_status(task_id, agent=agent_name, status="completed")
                print(f"   ✅ Task {task_id} completed")
                
            except Exception as e:
                print(f"   ❌ Task {task_id} processing failed: {e}")
        
        # Step 5: Get updated statistics
        print("\n5️⃣ Getting updated statistics...")
        try:
            new_task_count = client.get_agent_task_count(agent_name, days=1)
            print(f"   📊 Tasks completed today: {new_task_count.get('completed_tasks', 0)}")
            
            recent_tasks = client.list_recent_tasks(agent_name, limit=5)
            print(f"   📋 Recent tasks: {len(recent_tasks)} found")
            
            for task in recent_tasks[:3]:  # Show first 3
                task_id = task.get('task_id', 'Unknown')
                status = task.get('status', 'Unknown')
                print(f"      - Task {task_id}: {status}")
                
        except Exception as e:
            print(f"   ⚠️  Updated statistics unavailable: {e}")
        
        print("\n🎉 Workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n💥 Workflow failed: {e}")
        return False


def bulk_task_assignment():
    """Example of bulk task assignment with error handling"""
    
    client = MCPClient()
    agent_name = "bulk_agent"
    
    print("📦 Bulk Task Assignment Example")
    print("=" * 40)
    
    # Assign 10 tasks
    task_ids = range(6001, 6011)  # Tasks 6001 to 6010
    
    try:
        for task_id in task_ids:
            try:
                result = client.assign_task(agent_name, task_id)
                print(f"✅ Task {task_id}: {result.get('status', 'assigned')}")
            except Exception as e:
                print(f"❌ Task {task_id}: {e}")
    
    except Exception as e:
        print(f"💥 Bulk assignment failed: {e}")


def monitoring_dashboard():
    """Example of creating a simple monitoring dashboard"""
    
    client = MCPClient()
    agents = ["agent_1", "agent_2", "agent_3"]
    
    print("📊 Agent Monitoring Dashboard")
    print("=" * 40)
    
    for agent in agents:
        try:
            # Get stats for each agent
            task_count = client.get_agent_task_count(agent, days=7)
            recent_tasks = client.list_recent_tasks(agent, limit=3)
            avg_time = client.average_completion_time(agent)
            
            print(f"\n🤖 Agent: {agent}")
            print(f"   📊 Tasks (7 days): {task_count.get('completed_tasks', 0)}")
            print(f"   📋 Recent tasks: {len(recent_tasks)}")
            print(f"   ⏱️  Avg time: {avg_time.get('average_completion_time_seconds', 0):.2f}s")
            
        except Exception as e:
            print(f"\n🤖 Agent: {agent}")
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("🎯 MCP Client Workflow Examples")
    print("=" * 50)
    
    # Run different examples
    print("\n" + "="*50)
    agent_workflow()
    
    print("\n" + "="*50)
    bulk_task_assignment()
    
    print("\n" + "="*50)
    monitoring_dashboard()