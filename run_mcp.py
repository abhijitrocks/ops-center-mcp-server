#!/usr/bin/env python3
"""
MCP Server and Client Runner
Utility script to start the server and interact with it using the client
"""

import subprocess
import sys
import time
import signal
import argparse
from pathlib import Path
import json


def start_server(port: int = 8000, host: str = "0.0.0.0"):
    """Start the MCP server using uvicorn"""
    print(f"Starting MCP server on {host}:{port}...")
    
    cmd = [
        "uvicorn", 
        "main:app", 
        "--host", host, 
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        print(f"Server started with PID: {process.pid}")
        print(f"Server URL: http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        process.wait()
        print("Server stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


def start_rpc_server(port: int = 8001, host: str = "0.0.0.0"):
    """Start the RPC server separately"""
    print(f"Starting RPC server on {host}:{port}...")
    
    cmd = [
        "uvicorn", 
        "rpc_server:app", 
        "--host", host, 
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        print(f"RPC Server started with PID: {process.pid}")
        print(f"RPC Server URL: http://{host}:{port}")
        print("Press Ctrl+C to stop the RPC server")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down RPC server...")
        process.terminate()
        process.wait()
        print("RPC Server stopped")
    except Exception as e:
        print(f"Error starting RPC server: {e}")
        sys.exit(1)


def test_client(env: str = "local", agent: str = "test_agent"):
    """Run the MCP client tests"""
    print(f"Testing MCP client against {env} environment...")
    
    cmd = ["python", "test_mcp_client.py", "--env", env, "--agent", agent]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Client tests completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Client tests failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Error running client tests: {e}")
        return False


def run_example():
    """Run the example client usage script"""
    print("Running example client usage...")
    
    cmd = ["python", "example_client_usage.py"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Example completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Example failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Error running example: {e}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies from requirements.txt...")
    
    cmd = ["pip", "install", "-r", "requirements.txt"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False


def show_client_usage():
    """Show client usage examples"""
    print("MCP Client Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "description": "Health check",
            "command": "python mcp_client.py --agent test_agent --action health"
        },
        {
            "description": "Get agent task count",
            "command": "python mcp_client.py --agent test_agent --action task_count --days 7"
        },
        {
            "description": "List recent tasks",
            "command": "python mcp_client.py --agent test_agent --action recent_tasks --limit 5"
        },
        {
            "description": "Assign a task",
            "command": "python mcp_client.py --agent test_agent --action assign --task-id 1234"
        },
        {
            "description": "Update task status",
            "command": "python mcp_client.py --agent test_agent --action update_status --task-id 1234 --status completed"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}:")
        print(f"   {example['command']}")
        print()
    
    print("Python API Examples:")
    print("=" * 20)
    print("from mcp_client import MCPClient")
    print("client = MCPClient()")
    print("health = client.health_check()")
    print("tasks = client.list_recent_tasks('agent_name')")
    print()


def check_server_running(url: str = "http://localhost:8000") -> bool:
    """Check if server is running"""
    try:
        import requests
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MCP Server and Client Runner")
    parser.add_argument("action", choices=[
        "server", "rpc-server", "test", "example", "install", "help", "status"
    ], help="Action to perform")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--env", default="local", help="Environment for testing")
    parser.add_argument("--agent", default="test_agent", help="Agent name for testing")
    
    args = parser.parse_args()
    
    if args.action == "server":
        start_server(args.port, args.host)
    
    elif args.action == "rpc-server":
        start_rpc_server(args.port, args.host)
    
    elif args.action == "test":
        # Check if server is running
        server_url = f"http://localhost:{args.port}"
        if not check_server_running(server_url):
            print(f"Warning: Server doesn't appear to be running at {server_url}")
            print("You may need to start the server first with: python run_mcp.py server")
            print("Continuing with test anyway...")
        
        success = test_client(args.env, args.agent)
        sys.exit(0 if success else 1)
    
    elif args.action == "example":
        # Check if server is running
        server_url = f"http://localhost:{args.port}"
        if not check_server_running(server_url):
            print(f"Warning: Server doesn't appear to be running at {server_url}")
            print("You may need to start the server first with: python run_mcp.py server")
            print("Continuing with example anyway...")
        
        success = run_example()
        sys.exit(0 if success else 1)
    
    elif args.action == "install":
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    elif args.action == "help":
        show_client_usage()
    
    elif args.action == "status":
        server_url = f"http://localhost:{args.port}"
        if check_server_running(server_url):
            print(f"✓ Server is running at {server_url}")
            try:
                from mcp_client import MCPClient, MCPClientConfig
                config = MCPClientConfig(server_url=server_url)
                client = MCPClient(config)
                health = client.health_check()
                print(f"  Health status: {health}")
            except Exception as e:
                print(f"  Error checking health: {e}")
        else:
            print(f"✗ Server is not running at {server_url}")
        
        # Check config file
        config_file = Path("mcp_config.json")
        if config_file.exists():
            print("✓ Configuration file found")
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    print(f"  Default environment: {config.get('default_environment')}")
                    envs = list(config.get('environments', {}).keys())
                    print(f"  Available environments: {', '.join(envs)}")
            except Exception as e:
                print(f"  Error reading config: {e}")
        else:
            print("⚠ Configuration file not found")


if __name__ == "__main__":
    main()