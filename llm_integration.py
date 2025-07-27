#!/usr/bin/env python3
"""
LLM Integration for MCP Chat Interface
Adds intelligent conversation capabilities while maintaining rule-based fallback
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio

# LLM Integration Options
LLM_PROVIDERS = {
    "openai": {
        "available": False,
        "module": "openai",
        "model": "gpt-4",
        "api_key_env": "OPENAI_API_KEY"
    },
    "anthropic": {
        "available": False,
        "module": "anthropic", 
        "model": "claude-3-sonnet-20240229",
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "ollama": {
        "available": False,
        "module": "ollama",
        "model": "phi3:mini",
        "api_key_env": None  # Local model
    },
    "huggingface": {
        "available": False,
        "module": "transformers",
        "model": "microsoft/DialoGPT-medium",
        "api_key_env": "HUGGINGFACE_API_KEY"
    }
}

class LLMCommandProcessor:
    """
    LLM-powered command processor for MCP Chat Interface
    Provides intelligent conversation while maintaining rule-based fallback
    """
    
    def __init__(self):
        self.llm_client = None
        self.provider = None
        self.available = False
        self.conversation_history = []
        self.max_history = 10
        
        # Try to initialize LLM providers
        self._initialize_llm()
        
        # MCP System context for the LLM
        self.system_context = self._build_system_context()
    
    def _initialize_llm(self):
        """Try to initialize available LLM providers"""
        import os
        
        # Try OpenAI first
        try:
            import openai
            if os.getenv("OPENAI_API_KEY"):
                self.llm_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.provider = "openai"
                self.available = True
                LLM_PROVIDERS["openai"]["available"] = True
                print("✅ OpenAI LLM initialized successfully")
                return
        except ImportError:
            pass
        
        # Try Anthropic
        try:
            import anthropic
            if os.getenv("ANTHROPIC_API_KEY"):
                self.llm_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                self.provider = "anthropic"
                self.available = True
                LLM_PROVIDERS["anthropic"]["available"] = True
                print("✅ Anthropic Claude LLM initialized successfully")
                return
        except ImportError:
            pass
        
        # Try Ollama (local)
        try:
            import ollama
            # Test if Ollama is running
            ollama.list()
            self.llm_client = ollama
            self.provider = "ollama"
            self.available = True
            LLM_PROVIDERS["ollama"]["available"] = True
            print("✅ Ollama local LLM initialized successfully")
            return
        except:
            pass
        
        print("⚠️ No LLM provider available - falling back to rule-based processing")
    
    def _build_system_context(self) -> str:
        """Build comprehensive system context for the LLM"""
        return """You are an intelligent assistant for the MCP (Multi-Agent Command Platform) system. 

SYSTEM CAPABILITIES:
- Agent Management: Create, list, and manage agents (abhijit, Chitra, ashish, ramesh, Aleem, bulk_agent, test_agent, workflow_agent)
- Workbench Operations: Manage workbenches (Dispute, Transaction, Account Holder, Loan) with role assignments
- Role Management: Assign roles (Assessor, Reviewer, Team Lead, Viewer) to agents in workbenches
- Task Management: Create, assign, and track tasks
- Analytics: Generate coverage reports and statistics

AVAILABLE COMMANDS:
- create-agent <name> - Create new agent
- create-workbench <name> "<description>" - Create new workbench
- create-task <id> [agent] [workbench_id] - Create new task
- agents / list agents - Show all agents
- workbenches - Show all workbenches
- roles <workbench_id> - Show roles in workbench
- assign-role <agent> <workbench_id> <role> - Assign role to agent
- agent-roles <agent> - Show agent's roles
- coverage - Show role coverage report

CONVERSATION STYLE:
- Be helpful and conversational
- Understand natural language requests
- Provide clear explanations
- Suggest relevant actions
- Handle follow-up questions intelligently
- When you need to execute commands, use the exact command format above

CONTEXT AWARENESS:
- Remember previous conversation context
- Handle pronouns and references ("their workbenches", "that agent")
- Provide relevant suggestions based on current state
- Explain system concepts when needed

Your goal is to make the MCP system easy to use through natural conversation while executing the appropriate commands to fulfill user requests."""

    async def process_with_llm(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message with LLM intelligence"""
        if not self.available:
            return {"error": "LLM not available", "fallback_to_rules": True}
        
        try:
            # Build conversation context
            messages = self._build_conversation_context(user_message, context)
            
            # Get LLM response
            if self.provider == "openai":
                response = await self._call_openai(messages)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(messages)
            elif self.provider == "ollama":
                response = await self._call_ollama(messages)
            else:
                return {"error": "Unknown LLM provider", "fallback_to_rules": True}
            
            # Parse LLM response for commands and natural language
            parsed_response = self._parse_llm_response(response, user_message)
            
            # Update conversation history
            self._update_conversation_history(user_message, response)
            
            return parsed_response
            
        except Exception as e:
            print(f"LLM processing error: {e}")
            return {"error": f"LLM error: {str(e)}", "fallback_to_rules": True}
    
    def _build_conversation_context(self, user_message: str, context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Build conversation context for LLM"""
        messages = [{"role": "system", "content": self.system_context}]
        
        # Add recent conversation history
        for msg in self.conversation_history[-self.max_history:]:
            messages.append({"role": "user", "content": msg["user"]})
            messages.append({"role": "assistant", "content": msg["assistant"]})
        
        # Add current context if available
        if context:
            context_info = f"Current system context: {json.dumps(context, indent=2)}"
            messages.append({"role": "system", "content": context_info})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API"""
        response = self.llm_client.chat.completions.create(
            model=LLM_PROVIDERS["openai"]["model"],
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """Call Anthropic Claude API"""
        # Convert messages to Claude format
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        conversation = [m for m in messages if m["role"] != "system"]
        
        response = self.llm_client.messages.create(
            model=LLM_PROVIDERS["anthropic"]["model"],
            system=system_msg,
            messages=conversation,
            max_tokens=500
        )
        return response.content[0].text
    
    async def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama local LLM"""
        # Convert to Ollama format
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        response = self.llm_client.generate(
            model=LLM_PROVIDERS["ollama"]["model"],
            prompt=prompt
        )
        return response['response']
    
    def _parse_llm_response(self, llm_response: str, original_message: str) -> Dict[str, Any]:
        """Parse LLM response to extract commands and natural language"""
        
        # Look for commands in the response
        commands = self._extract_commands_from_response(llm_response)
        
        if commands:
            return {
                "type": "llm_with_commands",
                "natural_response": llm_response,
                "commands": commands,
                "original_message": original_message,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "type": "llm_response",
                "message": llm_response,
                "original_message": original_message,
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_commands_from_response(self, response: str) -> List[str]:
        """Extract MCP commands from LLM response"""
        commands = []
        
        # Common command patterns
        command_patterns = [
            r'(create-agent\s+\w+)',
            r'(create-workbench\s+\w+(?:\s+"[^"]*")?)',
            r'(create-task\s+\d+(?:\s+\w+)?(?:\s+\d+)?)',
            r'(assign-role\s+\w+\s+\d+\s+\w+)',
            r'(agents?)',
            r'(workbenches?)',
            r'(roles\s+\d+)',
            r'(agent-roles\s+\w+)',
            r'(coverage)',
            r'(stats\s+\w+)'
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            commands.extend(matches)
        
        return commands
    
    def _update_conversation_history(self, user_message: str, llm_response: str):
        """Update conversation history"""
        self.conversation_history.append({
            "user": user_message,
            "assistant": llm_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Get LLM integration status"""
        return {
            "available": self.available,
            "provider": self.provider,
            "model": LLM_PROVIDERS.get(self.provider, {}).get("model", "Unknown") if self.provider else None,
            "conversation_length": len(self.conversation_history),
            "providers": LLM_PROVIDERS
        }
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def set_model(self, provider: str, model: str = None):
        """Switch LLM provider/model"""
        if provider in LLM_PROVIDERS and LLM_PROVIDERS[provider]["available"]:
            self.provider = provider
            if model:
                LLM_PROVIDERS[provider]["model"] = model
            self._initialize_llm()
            return True
        return False

# Factory function to create LLM processor
def create_llm_processor() -> LLMCommandProcessor:
    """Create and return LLM processor instance"""
    return LLMCommandProcessor()

# Test LLM availability
def test_llm_availability() -> Dict[str, Any]:
    """Test which LLM providers are available"""
    import os
    
    results = {}
    
    # Test OpenAI
    try:
        import openai
        has_key = bool(os.getenv("OPENAI_API_KEY"))
        results["openai"] = {"module_available": True, "api_key_available": has_key}
    except ImportError:
        results["openai"] = {"module_available": False, "api_key_available": False}
    
    # Test Anthropic
    try:
        import anthropic
        has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        results["anthropic"] = {"module_available": True, "api_key_available": has_key}
    except ImportError:
        results["anthropic"] = {"module_available": False, "api_key_available": False}
    
    # Test Ollama
    try:
        import ollama
        ollama.list()  # Test if service is running
        results["ollama"] = {"module_available": True, "service_running": True}
    except:
        results["ollama"] = {"module_available": False, "service_running": False}
    
    return results

if __name__ == "__main__":
    # Test LLM integration
    print("🤖 Testing LLM Integration...")
    
    # Check availability
    availability = test_llm_availability()
    print(f"\n📊 LLM Provider Availability:")
    for provider, status in availability.items():
        print(f"  {provider}: {status}")
    
    # Create processor
    processor = create_llm_processor()
    status = processor.get_llm_status()
    
    print(f"\n🔧 LLM Processor Status:")
    print(f"  Available: {status['available']}")
    print(f"  Provider: {status['provider']}")
    print(f"  Model: {status['model']}")
    
    if status['available']:
        print("\n✅ LLM integration ready!")
        print("💡 You can now use natural language with the MCP Chat Interface!")
    else:
        print("\n⚠️ LLM not available - install providers and set API keys:")
        print("  pip install openai anthropic ollama transformers")
        print("  export OPENAI_API_KEY=your_key")
        print("  export ANTHROPIC_API_KEY=your_key")