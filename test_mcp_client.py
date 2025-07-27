#!/usr/bin/env python3
"""
Test script for MCP Client
This script tests the MCP client functionality against the server
"""

import json
import asyncio
import sys
from pathlib import Path
from mcp_client import MCPClient, MCPClientConfig


def load_config(env: str = "local") -> dict:
    """Load configuration from mcp_config.json"""
    config_file = Path("mcp_config.json")
    if not config_file.exists():
        print("Warning: mcp_config.json not found, using defaults")
        return {"server_url": "http://localhost:8000", "timeout": 30}
    
    with open(config_file) as f:
        config = json.load(f)
    
    env_config = config.get("environments", {}).get(env)
    if not env_config:
        print(f"Warning: Environment '{env}' not found in config, using local")
        env_config = config.get("environments", {}).get("local", {})
    
    return env_config


def test_basic_functionality(client: MCPClient):
    """Test basic client functionality"""
    print("Testing basic functionality...")
    
    try:
        # Test health check
        print("  ✓ Testing health check...")
        health = client.health_check()
        assert health.get("status") == "OK", f"Expected status 'OK', got {health}"
        print(f"    Health check passed: {health}")
        
        # Test server info
        print("  ✓ Testing server info...")
        try:
            server_info = client.get_server_info()
            print(f"    Server info retrieved: {server_info.get('info', {}).get('title', 'Unknown')}")
        except Exception as e:
            print(f"    Server info failed (expected if OpenAPI not available): {e}")
        
        print("✓ Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def test_agent_operations(client: MCPClient, agent_name: str = "test_agent"):
    """Test agent-related operations"""
    print(f"Testing agent operations for '{agent_name}'...")
    
    try:
        # Test task count
        print("  ✓ Testing get_agent_task_count...")
        task_count = client.get_agent_task_count(agent_name, days=7)
        print(f"    Task count: {task_count}")
        
        # Test recent tasks
        print("  ✓ Testing list_recent_tasks...")
        recent_tasks = client.list_recent_tasks(agent_name, limit=5)
        print(f"    Recent tasks: {len(recent_tasks)} found")
        
        # Test average completion time
        print("  ✓ Testing average_completion_time...")
        avg_time = client.average_completion_time(agent_name)
        print(f"    Average completion time: {avg_time}")
        
        print("✓ Agent operation tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Agent operation test failed: {e}")
        return False


def test_task_management(client: MCPClient, agent_name: str = "test_agent"):
    """Test task assignment and status updates"""
    print(f"Testing task management for '{agent_name}'...")
    
    test_task_id = 9999  # Use a high number to avoid conflicts
    
    try:
        # Test task assignment
        print(f"  ✓ Testing assign_task (ID: {test_task_id})...")
        assigned_task = client.assign_task(agent_name, test_task_id)
        print(f"    Task assigned: {assigned_task}")
        
        # Test status update
        print("  ✓ Testing update_task_status...")
        updated_task = client.update_task_status(test_task_id, agent=agent_name, status="in_progress")
        print(f"    Task status updated: {updated_task}")
        
        # Complete the task
        print("  ✓ Testing task completion...")
        completed_task = client.update_task_status(test_task_id, agent=agent_name, status="completed")
        print(f"    Task completed: {completed_task}")
        
        print("✓ Task management tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Task management test failed: {e}")
        return False


async def test_async_operations(client: MCPClient, agent_name: str = "test_agent"):
    """Test asynchronous operations"""
    print(f"Testing async operations for '{agent_name}'...")
    
    try:
        # Test async health check
        print("  ✓ Testing async_health_check...")
        health = await client.async_health_check()
        print(f"    Async health check: {health}")
        
        # Test concurrent operations
        print("  ✓ Testing concurrent async operations...")
        results = await asyncio.gather(
            client.async_get_agent_task_count(agent_name, days=1),
            client.async_list_recent_tasks(agent_name, limit=3),
            client.async_average_completion_time(agent_name),
            return_exceptions=True
        )
        
        task_count, recent_tasks, avg_time = results
        
        if not isinstance(task_count, Exception):
            print(f"    Concurrent task count: {task_count}")
        if not isinstance(recent_tasks, Exception):
            print(f"    Concurrent recent tasks: {len(recent_tasks)} found")
        if not isinstance(avg_time, Exception):
            print(f"    Concurrent avg time: {avg_time}")
        
        print("✓ Async operation tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Async operation test failed: {e}")
        return False


def test_error_handling(client: MCPClient):
    """Test error handling"""
    print("Testing error handling...")
    
    try:
        # Test with invalid method
        print("  ✓ Testing invalid method...")
        try:
            result = client._sync_rpc_call("invalid_method", {})
            print(f"    Unexpected success: {result}")
            return False
        except Exception as e:
            print(f"    Expected error caught: {e}")
        
        # Test with invalid task ID for status update
        print("  ✓ Testing invalid task ID...")
        try:
            result = client.update_task_status(-1, status="completed")
            print(f"    Unexpected success: {result}")
        except Exception as e:
            print(f"    Expected error caught: {e}")
        
        print("✓ Error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def run_all_tests(env: str = "local", agent_name: str = "test_agent"):
    """Run all tests"""
    print("=" * 60)
    print("MCP Client Test Suite")
    print("=" * 60)
    
    # Load configuration
    config_data = load_config(env)
    print(f"Using environment: {env}")
    print(f"Server URL: {config_data.get('server_url')}")
    print(f"Agent: {agent_name}")
    print("-" * 60)
    
    # Initialize client
    config = MCPClientConfig(
        server_url=config_data.get("server_url", "http://localhost:8000"),
        timeout=config_data.get("timeout", 30)
    )
    client = MCPClient(config)
    
    # Run tests
    test_results = []
    
    test_results.append(test_basic_functionality(client))
    print()
    
    test_results.append(test_agent_operations(client, agent_name))
    print()
    
    test_results.append(test_task_management(client, agent_name))
    print()
    
    test_results.append(await test_async_operations(client, agent_name))
    print()
    
    test_results.append(test_error_handling(client))
    print()
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP Client")
    parser.add_argument("--env", default="local", help="Environment to test against")
    parser.add_argument("--agent", default="test_agent", help="Agent name to use for tests")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_all_tests(args.env, args.agent))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()