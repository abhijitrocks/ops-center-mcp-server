#!/bin/bash

# MCP Chat Interface Startup Script
echo "🚀 Starting MCP Chat Interface..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    exit 1
fi

# Check for required dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, jinja2, websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required dependencies..."
    pip install fastapi uvicorn jinja2 python-multipart websockets --break-system-packages
fi

# Create necessary directories
mkdir -p templates static

echo "🔧 Starting web server..."
echo "📱 Chat interface will be available at: http://localhost:8080"
echo "🔗 Share this URL with others to give them access to the MCP system"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 web_chat_interface.py