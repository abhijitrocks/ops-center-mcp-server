#!/usr/bin/env python3
"""
Startup script for MCP Chat Interface
Ensures proper initialization for cloud deployments
"""

import os
import sys
import subprocess

def main():
    """Main startup function"""
    print("🚀 MCP Chat Interface Startup Script")
    print("=" * 50)
    
    # Set environment variables
    PORT = os.getenv("PORT", "8080")
    HOST = os.getenv("HOST", "0.0.0.0")
    
    print(f"📱 Starting server on {HOST}:{PORT}")
    
    # Create necessary directories
    os.makedirs("templates", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Start the server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "web_chat_interface:app",
            "--host", str(HOST),
            "--port", str(PORT),
            "--workers", "1"
        ]
        
        print(f"🔧 Executing: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()