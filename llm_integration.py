"""
LLM Integration for MCP Chat Interface
Supports multiple LLM providers with fallback to rule-based processing
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

# LLM Provider configurations
LLM_PROVIDERS = {
    "ollama": {
        "name": "Ollama (Local)",
        "api_url": "http://localhost:11434/api/generate",
        "model": "phi3:mini",
        "headers": {"Content-Type": "application/json"},
        "env_vars": []  # No API key needed for local Ollama
    },
    "openai": {
        "name": "OpenAI GPT",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
        "headers": {"Content-Type": "application/json"},
        "env_vars": ["OPENAI_API_KEY"]
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "api_url": "https://api.anthropic.com/v1/messages",
        "model": "claude-3-haiku-20240307",
        "headers": {"Content-Type": "application/json"},
        "env_vars": ["ANTHROPIC_API_KEY"]
    },
    "huggingface": {
        "name": "HuggingFace",
        "api_url": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        "model": "microsoft/DialoGPT-medium",
        "headers": {"Content-Type": "application/json"},
        "env_vars": ["HUGGINGFACE_API_KEY"]
    }
}

class LLMCommandProcessor:
    def __init__(self):
        self.provider = None
        self.client_config = None
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # Try to initialize LLM client
        self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize LLM client with available provider"""
        # Try providers in order of preference
        for provider_key in ["ollama", "openai", "anthropic", "huggingface"]:
            provider = LLM_PROVIDERS[provider_key]
            
            # Check if required environment variables are set
            if provider["env_vars"]:
                missing_vars = [var for var in provider["env_vars"] if not os.getenv(var)]
                if missing_vars:
                    print(f"⚠️  {provider['name']}: Missing environment variables: {missing_vars}")
                    continue
            
            # Test provider availability
            if self._test_provider_availability(provider_key):
                self.provider = provider_key
                self.client_config = provider
                print(f"✅ LLM Integration: {provider['name']} is ready!")
                return
            else:
                print(f"❌ {provider['name']}: Not available")
        
        print("⚠️  No LLM provider available. Using rule-based processing only.")
    
    def _test_provider_availability(self, provider_key: str) -> bool:
        """Test if a provider is available and responding"""
        provider = LLM_PROVIDERS[provider_key]
        
        try:
            if provider_key == "ollama":
                # Test Ollama with a simple request
                response = requests.post(
                    provider["api_url"],
                    json={
                        "model": provider["model"],
                        "prompt": "Hello",
                        "stream": False
                    },
                    timeout=5
                )
                return response.status_code == 200
            
            elif provider_key == "openai":
                # Test OpenAI API
                headers = {**provider["headers"], "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
                response = requests.post(
                    provider["api_url"],
                    headers=headers,
                    json={
                        "model": provider["model"],
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 10
                    },
                    timeout=5
                )
                return response.status_code == 200
            
            # Add other provider tests as needed
            return False
            
        except Exception as e:
            print(f"⚠️  {provider['name']} test failed: {e}")
            return False
    
    def _build_system_context(self) -> str:
        """Build system context for LLM"""
        return """You are an AI assistant for the MCP (Multi-Agent Coordination Platform) system. 

AVAILABLE MCP COMMANDS:
- agents: List all agents
- agent-details <name>: Get detailed info about an agent
- workbenches: List all workbenches  
- workbench-details <id>: Get workbench details
- roles <workbench_id>: List roles in a workbench
- assign-role <agent> <role> <workbench_id>: Assign role to agent
- coverage: Show role coverage report
- tasks: List recent tasks
- create-agent <name>: Create new agent
- create-workbench <name> [description]: Create new workbench
- create-task <agent> <description>: Create new task

RESPONSE FORMAT:
When users ask questions, respond naturally but also suggest relevant MCP commands. 
For direct command requests, extract and format the exact MCP command.

EXAMPLES:
User: "How many agents do we have?"
Response: "Let me check the current agents for you. [MCP_COMMAND: agents]"

User: "Create an agent named Sarah"
Response: "I'll create a new agent named Sarah. [MCP_COMMAND: create-agent Sarah]"

Always be helpful and suggest the most relevant MCP commands for the user's needs."""

    def process_with_llm(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message with LLM and extract commands"""
        if not self.provider:
            return {"error": "No LLM provider available", "fallback_to_rules": True}
        
        try:
            # Build conversation context
            system_context = self._build_system_context()
            
            # Add current context if available
            context_info = ""
            if context and context.get("last_command_context"):
                context_info = f"\nCONTEXT: {context['last_command_context']}"
            
            # Prepare the conversation
            full_prompt = f"{system_context}{context_info}\n\nUser: {user_message}\nAssistant:"
            
            # Call LLM API
            llm_response = self._call_llm_api(full_prompt)
            
            if llm_response:
                # Extract commands from response
                commands = self._extract_commands_from_response(llm_response)
                
                # Update conversation history
                self.conversation_history.append({
                    "user": user_message,
                    "assistant": llm_response,
                    "timestamp": datetime.now().isoformat(),
                    "commands": commands
                })
                
                # Keep only recent history
                if len(self.conversation_history) > self.max_history:
                    self.conversation_history = self.conversation_history[-self.max_history:]
                
                return {
                    "response": llm_response,
                    "commands": commands,
                    "provider": self.provider,
                    "success": True
                }
            else:
                return {"error": "LLM API call failed", "fallback_to_rules": True}
                
        except Exception as e:
            print(f"❌ LLM processing error: {e}")
            return {"error": str(e), "fallback_to_rules": True}
    
    def _call_llm_api(self, prompt: str) -> Optional[str]:
        """Call the configured LLM API"""
        if not self.client_config:
            return None
        
        try:
            if self.provider == "ollama":
                response = requests.post(
                    self.client_config["api_url"],
                    json={
                        "model": self.client_config["model"],
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
            
            elif self.provider == "openai":
                headers = {**self.client_config["headers"], "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
                response = requests.post(
                    self.client_config["api_url"],
                    headers=headers,
                    json={
                        "model": self.client_config["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
            
            # Add other providers as needed
            
        except Exception as e:
            print(f"❌ LLM API call failed: {e}")
            return None
        
        return None
    
    def _extract_commands_from_response(self, response: str) -> List[str]:
        """Extract MCP commands from LLM response"""
        commands = []
        
        # Look for [MCP_COMMAND: ...] patterns
        command_pattern = r'\[MCP_COMMAND:\s*([^\]]+)\]'
        matches = re.findall(command_pattern, response, re.IGNORECASE)
        
        for match in matches:
            commands.append(match.strip())
        
        # If no explicit commands found, try to infer from common patterns
        if not commands:
            response_lower = response.lower()
            
            # Common command patterns
            if "list agents" in response_lower or "show agents" in response_lower:
                commands.append("agents")
            elif "list workbenches" in response_lower or "show workbenches" in response_lower:
                commands.append("workbenches")
            elif "coverage" in response_lower or "role coverage" in response_lower:
                commands.append("coverage")
            elif "create agent" in response_lower:
                # Try to extract agent name
                agent_match = re.search(r'create agent\s+(\w+)', response_lower)
                if agent_match:
                    commands.append(f"create-agent {agent_match.group(1)}")
        
        return commands
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Get current LLM integration status"""
        return {
            "enabled": self.provider is not None,
            "provider": self.provider,
            "provider_name": self.client_config["name"] if self.client_config else None,
            "model": self.client_config["model"] if self.client_config else None,
            "conversation_length": len(self.conversation_history),
            "available_providers": [
                {
                    "key": key,
                    "name": config["name"],
                    "available": self._test_provider_availability(key)
                }
                for key, config in LLM_PROVIDERS.items()
            ]
        }

# Factory function to create LLM processor
def create_llm_processor() -> LLMCommandProcessor:
    """Create and return LLM command processor"""
    return LLMCommandProcessor()

# Test function to check LLM availability
def test_llm_availability() -> Dict[str, Any]:
    """Test which LLM providers are available"""
    processor = LLMCommandProcessor()
    return processor.get_llm_status()

if __name__ == "__main__":
    # Test LLM integration
    print("🔍 Testing LLM Integration...")
    processor = create_llm_processor()
    status = processor.get_llm_status()
    
    print(f"\n📊 LLM Status:")
    print(f"  Enabled: {status['enabled']}")
    if status['enabled']:
        print(f"  Provider: {status['provider_name']}")
        print(f"  Model: {status['model']}")
    
    print(f"\n🔌 Available Providers:")
    for provider in status['available_providers']:
        status_icon = "✅" if provider['available'] else "❌"
        print(f"  {status_icon} {provider['name']}")
    
    # Test a sample query if LLM is available
    if status['enabled']:
        print(f"\n🧪 Testing sample query...")
        result = processor.process_with_llm("How many agents do we have?")
        if result.get('success'):
            print(f"✅ LLM Response: {result['response']}")
            if result['commands']:
                print(f"🎯 Extracted Commands: {result['commands']}")
        else:
            print(f"❌ Test failed: {result.get('error')}")