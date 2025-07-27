#!/usr/bin/env python3
"""
Simple MCP Client Test Script
This tests the client step by step with clear output
"""

from mcp_client import MCPClient, MCPClientConfig
import requests
import json

def test_server_direct():
    """Test the server directly with requests"""
    print("🔍 Testing server directly...")
    
    # Test RPC endpoint
    url = "http://localhost:8000/rpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "get_agent_task_count",
        "params": {"agent": "test_agent", "days": 7},
        "id": 1
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_client_rpc_call():
    """Test the client's RPC call method directly"""
    print("\n🔍 Testing client RPC call...")
    
    client = MCPClient()
    
    try:
        # Test direct RPC call
        result = client._sync_rpc_call("get_agent_task_count", {"agent": "test_agent", "days": 7})
        print(f"   RPC Result: {result}")
        return True
    except Exception as e:
        print(f"   RPC Error: {e}")
        return False

def test_client_methods():
    """Test each client method individually"""
    print("\n🔍 Testing client methods...")
    
    client = MCPClient()
    agent_name = "test_agent"
    
    # Test 1: Task count
    try:
        result = client.get_agent_task_count(agent_name, days=7)
        print(f"   ✅ Task count: {result}")
    except Exception as e:
        print(f"   ❌ Task count error: {e}")
    
    # Test 2: Assign task
    try:
        result = client.assign_task(agent_name, task_id=8888)
        print(f"   ✅ Assign task: {result}")
    except Exception as e:
        print(f"   ❌ Assign task error: {e}")
    
    # Test 3: Recent tasks
    try:
        result = client.list_recent_tasks(agent_name, limit=3)
        print(f"   ✅ Recent tasks: {result}")
    except Exception as e:
        print(f"   ❌ Recent tasks error: {e}")
    
    # Test 4: Average time
    try:
        result = client.average_completion_time(agent_name)
        print(f"   ✅ Average time: {result}")
    except Exception as e:
        print(f"   ❌ Average time error: {e}")
    
    # Test 5: Update status
    try:
        result = client.update_task_status(8888, agent=agent_name, status="completed")
        print(f"   ✅ Update status: {result}")
    except Exception as e:
        print(f"   ❌ Update status error: {e}")

def test_configuration():
    """Test different configurations"""
    print("\n🔍 Testing configurations...")
    
    # Test with custom config
    config = MCPClientConfig(
        server_url="http://localhost:8000",
        timeout=30
    )
    client = MCPClient(config)
    
    try:
        result = client.get_agent_task_count("test_agent", days=1)
        print(f"   ✅ Custom config works: {result}")
    except Exception as e:
        print(f"   ❌ Custom config error: {e}")

def test_error_handling():
    """Test error handling"""
    print("\n🔍 Testing error handling...")
    
    client = MCPClient()
    
    # Test invalid method
    try:
        result = client._sync_rpc_call("invalid_method", {})
        print(f"   ❌ Should have failed: {result}")
    except Exception as e:
        print(f"   ✅ Correctly caught error: {e}")

def main():
    """Run all tests"""
    print("🧪 Simple MCP Client Test")
    print("=" * 50)
    
    # Test 1: Direct server access
    server_ok = test_server_direct()
    
    if not server_ok:
        print("❌ Server is not responding. Make sure it's running!")
        return False
    
    # Test 2: Client RPC calls
    test_client_rpc_call()
    
    # Test 3: Client methods
    test_client_methods()
    
    # Test 4: Configuration
    test_configuration()
    
    # Test 5: Error handling
    test_error_handling()
    
    print("\n🎉 Testing completed!")
    return True

if __name__ == "__main__":
    main()