# 🧪 MCP Client Testing Guide

This guide shows you all the ways to test your MCP client to ensure it's working correctly.

## 🚀 Quick Start Testing

### 1. **Verify Server is Running**
```bash
# Check if RPC server is running
curl -X POST http://localhost:8000/rpc -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "get_agent_task_count", "params": {"agent": "test", "days": 1}, "id": 1}'
```

### 2. **Basic CLI Tests**
```bash
# Health check
python3 mcp_client.py --agent "test_agent" --action health

# Get task count
python3 mcp_client.py --agent "test_agent" --action task_count --days 7

# Assign a task
python3 mcp_client.py --agent "test_agent" --action assign --task-id 1234

# List recent tasks
python3 mcp_client.py --agent "test_agent" --action recent_tasks --limit 5

# Update task status
python3 mcp_client.py --agent "test_agent" --action update_status --task-id 1234 --status completed
```

## 🔧 Comprehensive Testing

### 1. **Simple Step-by-Step Test**
```bash
# Run the simple test script
python3 simple_test.py
```
This tests:
- ✅ Server connectivity
- ✅ RPC call functionality 
- ✅ All client methods
- ✅ Configuration options
- ✅ Error handling

### 2. **Full Test Suite**
```bash
# Run comprehensive tests
python3 test_mcp_client.py --env local --agent test_agent
```
This tests:
- ✅ Basic functionality
- ✅ Agent operations
- ✅ Task management
- ✅ Async operations
- ✅ Error handling

### 3. **Workflow Examples**
```bash
# Run real-world scenarios
python3 workflow_example.py
```
This demonstrates:
- ✅ Complete agent workflow
- ✅ Bulk task assignment
- ✅ Monitoring dashboard

## 🐍 Python API Testing

### 1. **Synchronous Testing**
```python
from mcp_client import MCPClient

# Test basic functionality
client = MCPClient()
health = client.health_check()
print(f"Health: {health}")

# Test agent operations
tasks = client.get_agent_task_count("test_agent", days=7)
print(f"Task count: {tasks}")

# Test task assignment
new_task = client.assign_task("test_agent", 1234)
print(f"Assigned: {new_task}")
```

### 2. **Asynchronous Testing**
```python
import asyncio
from mcp_client import MCPClient

async def test_async():
    client = MCPClient()
    
    # Test concurrent operations
    results = await asyncio.gather(
        client.async_health_check(),
        client.async_get_agent_task_count("test_agent", days=7),
        client.async_list_recent_tasks("test_agent", limit=5)
    )
    
    print(f"Results: {results}")

asyncio.run(test_async())
```

## 🔍 Manual Testing

### 1. **Test Server Endpoints**
```bash
# Direct RPC calls
curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "get_agent_task_count", "params": {"agent": "test", "days": 7}, "id": 1}'

curl -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "assign_task", "params": {"agent": "test", "task_id": 999}, "id": 2}'
```

### 2. **Test Different Configurations**
```bash
# Test against different servers
python3 mcp_client.py --server "http://localhost:8001" --agent "test" --action health
python3 mcp_client.py --server "https://your-server.com" --agent "test" --action health
```

## 🚦 Automated Testing

### 1. **Using the Utility Runner**
```bash
# Check overall status
python3 run_mcp.py status

# Run quick tests
python3 run_mcp.py test

# Start server and test
python3 run_mcp.py server &
sleep 5
python3 run_mcp.py test
```

### 2. **Environment Testing**
```bash
# Test different environments from config
python3 test_mcp_client.py --env local --agent test_agent
python3 test_mcp_client.py --env staging --agent staging_agent
python3 test_mcp_client.py --env production --agent prod_agent
```

## 📊 Performance Testing

### 1. **Concurrent Operations**
```python
import asyncio
from mcp_client import MCPClient

async def performance_test():
    client = MCPClient()
    
    # Test 10 concurrent operations
    tasks = []
    for i in range(10):
        tasks.append(client.async_assign_task("perf_agent", 2000 + i))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Completed {len([r for r in results if not isinstance(r, Exception)])} out of {len(tasks)} tasks")

asyncio.run(performance_test())
```

### 2. **Bulk Operations**
```python
from mcp_client import MCPClient
import time

client = MCPClient()

# Time bulk assignment
start = time.time()
for i in range(100):
    try:
        client.assign_task("bulk_agent", 3000 + i)
    except Exception as e:
        print(f"Task {3000 + i} failed: {e}")

end = time.time()
print(f"Assigned 100 tasks in {end - start:.2f} seconds")
```

## 🐛 Debugging

### 1. **Enable Verbose Output**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from mcp_client import MCPClient
client = MCPClient()
# Now all requests will be logged
```

### 2. **Check Server Logs**
```bash
# If running server locally
tail -f server.log

# Check server status
ps aux | grep uvicorn
netstat -tlnp | grep 8000
```

### 3. **Test Network Connectivity**
```bash
# Test if server is reachable
ping your-server.com
telnet localhost 8000
curl -v http://localhost:8000/rpc
```

## ✅ Expected Results

### **Successful Test Output:**
```
✅ Health check: {"status": "OK", "rpc_working": true}
✅ Task count: {"agent": "test_agent", "completed_tasks": 5}
✅ Task assignment: {"id": 123, "status": "assigned", "task_id": 1234}
✅ Recent tasks: [{"task_id": 1234, "status": "completed"}]
```

### **Common Error Messages:**
```
❌ Connection refused: Server not running
❌ 404 Not Found: Wrong endpoint or server
❌ RPC Error -32601: Method not found (invalid method name)
❌ Timeout: Server too slow or overloaded
```

## 🎯 Testing Checklist

- [ ] ✅ Server is running and accessible
- [ ] ✅ Health check works
- [ ] ✅ Task count retrieval works
- [ ] ✅ Task assignment works  
- [ ] ✅ Task status updates work
- [ ] ✅ Recent tasks listing works
- [ ] ✅ Error handling works correctly
- [ ] ✅ Async operations work
- [ ] ✅ Different configurations work
- [ ] ✅ CLI interface works
- [ ] ✅ Python API works

## 🚀 Quick Test Commands

```bash
# Complete test sequence
python3 simple_test.py                          # Basic functionality
python3 workflow_example.py                     # Real-world scenarios  
python3 test_mcp_client.py --agent test_agent   # Comprehensive suite
python3 run_mcp.py status                       # System status
```

Your MCP client is ready for production use! 🎉