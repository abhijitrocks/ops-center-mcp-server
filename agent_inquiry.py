#!/usr/bin/env python3
"""
Agent Inquiry Tool - Natural Language Interface for MCP Client
Ask questions about agents in natural language
"""

import argparse
import json
from mcp_client import MCPClient, MCPClientConfig


class AgentInquiry:
    """Natural language interface for agent queries"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        config = MCPClientConfig(server_url=server_url)
        self.client = MCPClient(config)
    
    def how_many_agents(self) -> str:
        """How many agents are there?"""
        try:
            result = self.client.list_agents()
            total = result.get('total_agents', 0)
            agents = result.get('agents', [])
            
            response = f"There are {total} agents in the system:\n"
            for i, agent in enumerate(agents, 1):
                response += f"  {i}. {agent}\n"
            
            return response
        except Exception as e:
            return f"Error getting agent count: {e}"
    
    def what_agents_exist(self) -> str:
        """What agents exist in the system?"""
        try:
            result = self.client.list_agents()
            agents = result.get('agents', [])
            
            if not agents:
                return "No agents found in the system."
            
            response = f"The following agents exist:\n"
            for i, agent in enumerate(agents, 1):
                response += f"  {i}. {agent}\n"
            
            return response
        except Exception as e:
            return f"Error listing agents: {e}"
    
    def agent_details(self, agent_name: str) -> str:
        """Get detailed information about a specific agent"""
        try:
            result = self.client.get_agent_info(agent_name)
            
            response = f"Agent: {result.get('agent', 'Unknown')}\n"
            response += f"Total Tasks: {result.get('total_tasks', 0)}\n"
            response += f"Completed Tasks: {result.get('completed_tasks', 0)}\n"
            response += f"In Progress Tasks: {result.get('in_progress_tasks', 0)}\n"
            response += f"Assigned Tasks: {result.get('assigned_tasks', 0)}\n"
            response += f"Completion Rate: {result.get('completion_rate', 0):.1f}%\n"
            
            recent_task = result.get('most_recent_task')
            if recent_task and recent_task.get('task_id'):
                response += f"Most Recent Task: #{recent_task.get('task_id')} ({recent_task.get('status')})\n"
            else:
                response += "Most Recent Task: None\n"
            
            return response
        except Exception as e:
            return f"Error getting agent details: {e}"
    
    def overall_stats(self, days: int = 7) -> str:
        """Get overall statistics for all agents"""
        try:
            result = self.client.get_agent_stats(days)
            
            response = f"Agent Statistics (Last {days} days):\n"
            response += "=" * 40 + "\n"
            
            summary = result.get('summary', {})
            response += f"Total Agents: {result.get('total_agents', 0)}\n"
            response += f"Total Tasks (All Agents): {summary.get('total_tasks_all_agents', 0)}\n"
            response += f"Total Completed (All Agents): {summary.get('total_completed_all_agents', 0)}\n"
            response += f"Overall Completion Rate: {summary.get('overall_completion_rate', 0):.1f}%\n\n"
            
            agents = result.get('agents', [])
            if agents:
                response += "Individual Agent Performance:\n"
                for agent in agents:
                    response += f"  • {agent.get('agent', 'Unknown')}:\n"
                    response += f"    - Tasks: {agent.get('total_tasks', 0)}\n"
                    response += f"    - Completed: {agent.get('completed_tasks', 0)}\n"
                    response += f"    - Rate: {agent.get('completion_rate', 0):.1f}%\n"
                    response += f"    - Avg Time: {agent.get('average_completion_time_seconds', 0):.1f}s\n\n"
            
            return response
        except Exception as e:
            return f"Error getting overall stats: {e}"
    
    def best_performing_agent(self, days: int = 7) -> str:
        """Who is the best performing agent?"""
        try:
            result = self.client.get_agent_stats(days)
            agents = result.get('agents', [])
            
            if not agents:
                return "No agents found with activity in the specified period."
            
            # Find best agent by completion rate, then by total completed tasks
            best_agent = max(agents, key=lambda x: (x.get('completion_rate', 0), x.get('completed_tasks', 0)))
            
            response = f"Best Performing Agent (Last {days} days):\n"
            response += f"🏆 {best_agent.get('agent', 'Unknown')}\n"
            response += f"   - Completion Rate: {best_agent.get('completion_rate', 0):.1f}%\n"
            response += f"   - Completed Tasks: {best_agent.get('completed_tasks', 0)}\n"
            response += f"   - Total Tasks: {best_agent.get('total_tasks', 0)}\n"
            response += f"   - Avg Completion Time: {best_agent.get('average_completion_time_seconds', 0):.1f}s\n"
            
            return response
        except Exception as e:
            return f"Error finding best performing agent: {e}"
    
    def slowest_agent(self, days: int = 7) -> str:
        """Which agent takes the longest to complete tasks?"""
        try:
            result = self.client.get_agent_stats(days)
            agents = result.get('agents', [])
            
            # Filter agents with completed tasks
            agents_with_completion = [a for a in agents if a.get('completed_tasks', 0) > 0]
            
            if not agents_with_completion:
                return "No agents found with completed tasks in the specified period."
            
            # Find slowest agent by average completion time
            slowest_agent = max(agents_with_completion, key=lambda x: x.get('average_completion_time_seconds', 0))
            
            response = f"Slowest Agent (Last {days} days):\n"
            response += f"🐌 {slowest_agent.get('agent', 'Unknown')}\n"
            response += f"   - Average Time: {slowest_agent.get('average_completion_time_seconds', 0):.1f}s\n"
            response += f"   - Completed Tasks: {slowest_agent.get('completed_tasks', 0)}\n"
            response += f"   - Completion Rate: {slowest_agent.get('completion_rate', 0):.1f}%\n"
            
            return response
        except Exception as e:
            return f"Error finding slowest agent: {e}"
    
    def process_question(self, question: str, agent_name: str = None, days: int = 7) -> str:
        """Process natural language questions about agents"""
        question_lower = question.lower()
        
        if "how many agents" in question_lower or "count" in question_lower:
            return self.how_many_agents()
        
        elif "what agents" in question_lower or "list agents" in question_lower or "agents exist" in question_lower:
            return self.what_agents_exist()
        
        elif "overall" in question_lower or "all agents" in question_lower or "summary" in question_lower:
            return self.overall_stats(days)
        
        elif "best" in question_lower or "top" in question_lower or "highest" in question_lower:
            return self.best_performing_agent(days)
        
        elif "slow" in question_lower or "longest" in question_lower or "worst" in question_lower:
            return self.slowest_agent(days)
        
        elif agent_name and ("about" in question_lower or "details" in question_lower or "info" in question_lower):
            return self.agent_details(agent_name)
        
        else:
            return self.show_help()
    
    def show_help(self) -> str:
        """Show available questions"""
        help_text = """
Available Questions:
==================
• "How many agents are there?"
• "What agents exist?"
• "Show me overall statistics"
• "Who is the best performing agent?"
• "Which agent is the slowest?"
• "Tell me about agent [agent_name]"

Examples:
---------
python3 agent_inquiry.py "How many agents are there?"
python3 agent_inquiry.py "Who is the best performing agent?"
python3 agent_inquiry.py "Tell me about test_agent" --agent test_agent
python3 agent_inquiry.py "Show overall stats" --days 30

Or use interactive mode:
python3 agent_inquiry.py --interactive
"""
        return help_text


def interactive_mode():
    """Interactive question and answer mode"""
    print("🤖 Agent Inquiry Interactive Mode")
    print("Type your questions about agents, or 'quit' to exit")
    print("Examples: 'How many agents?', 'Who is the best agent?', 'Show stats'")
    print("-" * 60)
    
    inquiry = AgentInquiry()
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            # Ask for agent name if needed
            agent_name = None
            if "about" in question.lower() or "details" in question.lower():
                agent_name = input("   Which agent? ").strip()
                if not agent_name:
                    print("   Please provide an agent name")
                    continue
            
            # Ask for days if needed
            days = 7
            if "days" in question.lower():
                try:
                    days_input = input("   How many days? (default: 7): ").strip()
                    if days_input:
                        days = int(days_input)
                except ValueError:
                    print("   Invalid number, using default (7 days)")
            
            print("\n💡 Answer:")
            answer = inquiry.process_question(question, agent_name, days)
            print(answer)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Ask questions about agents")
    parser.add_argument("question", nargs="?", help="Question to ask about agents")
    parser.add_argument("--agent", help="Specific agent name (for agent-specific questions)")
    parser.add_argument("--days", type=int, default=7, help="Number of days for statistics")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return
    
    if not args.question:
        inquiry = AgentInquiry(args.server)
        print(inquiry.show_help())
        return
    
    try:
        inquiry = AgentInquiry(args.server)
        answer = inquiry.process_question(args.question, args.agent, args.days)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()