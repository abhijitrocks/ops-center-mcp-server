#!/usr/bin/env python3
"""
Render.com startup script for MCP Chat Interface
Handles initialization, error handling, and proper port binding
"""

import os
import sys
import time
from pathlib import Path

def print_startup_info():
    """Print deployment information for debugging"""
    print("🚀 Starting MCP Chat Interface on Render.com")
    print(f"🐍 Python version: {sys.version}")
    print(f"🌍 Environment: {os.getenv('RENDER', 'Unknown')}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔌 Port: {os.getenv('PORT', 'Not set')}")
    print(f"🌐 Host: {os.getenv('HOST', 'Not set')}")
    
    # Check if critical files exist
    critical_files = ['web_chat_interface.py', 'requirements.txt']
    for file in critical_files:
        if Path(file).exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
    
    print("=" * 50)

def create_templates_dir():
    """Ensure templates directory exists for cloud deployment"""
    templates_dir = Path("templates")
    if not templates_dir.exists():
        print("📁 Creating templates directory...")
        templates_dir.mkdir(exist_ok=True)
        print("✅ Templates directory created")

def start_application():
    """Start the main application with error handling"""
    try:
        print("🔄 Importing application modules...")
        
        # Import after ensuring directories exist
        import uvicorn
        from web_chat_interface import app
        
        print("✅ Modules imported successfully")
        
        # Get port from environment (Render provides this)
        port = int(os.getenv("PORT", 8080))
        host = os.getenv("HOST", "0.0.0.0")
        
        print(f"🚀 Starting server on {host}:{port}")
        
        # Start uvicorn with appropriate settings for production
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This might be due to missing dependencies")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        print("💡 Check the logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    print_startup_info()
    create_templates_dir()
    start_application()