# 🤖 Agent Instructions Guide

This guide shows you how to give instructions and ask questions about agents through your MCP client.

## 🎯 **What You Can Ask About Agents**

### **1. How Many Agents Are There?**

#### **CLI Method:**
```bash
python3 mcp_client.py --agent "any" --action list_agents
```

#### **Natural Language:**
```bash
python3 agent_inquiry.py "How many agents are there?"
python3 agent_inquiry.py "What agents exist?"
```

#### **Python API:**
```python
from mcp_client import MCPClient

client = MCPClient()
result = client.list_agents()
print(f"Total agents: {result['total_agents']}")
print(f"Agents: {result['agents']}")
```

---

### **2. Get Detailed Agent Information**

#### **CLI Method:**
```bash
python3 mcp_client.py --agent "test_agent" --action agent_info
```

#### **Natural Language:**
```bash
python3 agent_inquiry.py "Tell me about test_agent" --agent test_agent
```

#### **Python API:**
```python
client = MCPClient()
info = client.get_agent_info("test_agent")
print(f"Agent: {info['agent']}")
print(f"Total Tasks: {info['total_tasks']}")
print(f"Completion Rate: {info['completion_rate']:.1f}%")
```

---

### **3. Get Overall Agent Statistics**

#### **CLI Method:**
```bash
python3 mcp_client.py --agent "any" --action agent_stats --days 7
```

#### **Natural Language:**
```bash
python3 agent_inquiry.py "Show overall stats"
python3 agent_inquiry.py "Show me all agent performance"
```

#### **Python API:**
```python
client = MCPClient()
stats = client.get_agent_stats(days=7)
print(f"Total agents: {stats['total_agents']}")
for agent in stats['agents']:
    print(f"- {agent['agent']}: {agent['completion_rate']:.1f}% completion rate")
```

---

### **4. Find Best/Worst Performing Agents**

#### **Natural Language:**
```bash
python3 agent_inquiry.py "Who is the best performing agent?"
python3 agent_inquiry.py "Which agent is the slowest?"
python3 agent_inquiry.py "Who has the highest completion rate?"
```

---

## 🗣️ **Natural Language Questions You Can Ask**

The `agent_inquiry.py` tool understands these types of questions:

### **Agent Count & Listing:**
- "How many agents are there?"
- "What agents exist in the system?"
- "List all agents"
- "Count the agents"

### **Performance Analysis:**
- "Who is the best performing agent?"
- "Which agent is the top performer?"
- "Who has the highest completion rate?"
- "Which agent is the slowest?"
- "Who takes the longest to complete tasks?"
- "Which agent is the worst performer?"

### **Overall Statistics:**
- "Show me overall statistics"
- "Give me a summary of all agents"
- "Show performance for all agents"
- "What's the overall completion rate?"

### **Specific Agent Details:**
- "Tell me about [agent_name]"
- "Show details for [agent_name]"
- "What's the info on [agent_name]?"

---

## 💬 **Interactive Mode**

For ongoing conversations about agents:

```bash
python3 agent_inquiry.py --interactive
```

This starts an interactive session where you can ask multiple questions:

```
🤖 Agent Inquiry Interactive Mode
Type your questions about agents, or 'quit' to exit
Examples: 'How many agents?', 'Who is the best agent?', 'Show stats'
------------------------------------------------------------

❓ Your question: How many agents are there?

💡 Answer:
There are 3 agents in the system:
  1. test_agent
  2. workflow_agent
  3. bulk_agent

❓ Your question: Who is the best agent?

💡 Answer:
Best Performing Agent (Last 7 days):
🏆 workflow_agent
   - Completion Rate: 100.0%
   - Completed Tasks: 3
   - Total Tasks: 3
   - Avg Completion Time: 2.0s
```

---

## 🔧 **All Available Commands**

### **CLI Commands:**
```bash
# List all agents
python3 mcp_client.py --agent "any" --action list_agents

# Get specific agent info
python3 mcp_client.py --agent "test_agent" --action agent_info

# Get all agent statistics
python3 mcp_client.py --agent "any" --action agent_stats --days 7

# Still works - get task count for specific agent
python3 mcp_client.py --agent "test_agent" --action task_count --days 7

# Assign tasks to agents
python3 mcp_client.py --agent "test_agent" --action assign --task-id 1234

# Update task status
python3 mcp_client.py --agent "test_agent" --action update_status --task-id 1234 --status completed
```

### **Natural Language Commands:**
```bash
# Questions about quantity and listing
python3 agent_inquiry.py "How many agents are there?"
python3 agent_inquiry.py "What agents exist?"

# Performance questions
python3 agent_inquiry.py "Who is the best performing agent?"
python3 agent_inquiry.py "Which agent is the slowest?"

# Statistics and summaries
python3 agent_inquiry.py "Show overall stats"
python3 agent_inquiry.py "Show performance for last 30 days" --days 30

# Specific agent details
python3 agent_inquiry.py "Tell me about workflow_agent" --agent workflow_agent

# Interactive mode
python3 agent_inquiry.py --interactive
```

---

## 📊 **Sample Outputs**

### **Agent List:**
```json
{
  "total_agents": 3,
  "agents": ["test_agent", "workflow_agent", "bulk_agent"],
  "limit": 100
}
```

### **Agent Details:**
```
Agent: test_agent
Total Tasks: 5
Completed Tasks: 2
In Progress Tasks: 0
Assigned Tasks: 3
Completion Rate: 40.0%
Most Recent Task: #9999 (assigned)
```

### **Overall Statistics:**
```
Agent Statistics (Last 7 days):
========================================
Total Agents: 3
Total Tasks (All Agents): 18
Total Completed (All Agents): 5
Overall Completion Rate: 27.8%

Individual Agent Performance:
  • test_agent: 40.0% completion rate
  • workflow_agent: 100.0% completion rate  
  • bulk_agent: 0.0% completion rate
```

---

## 🚀 **Quick Examples**

### **Find out how many agents:**
```bash
python3 agent_inquiry.py "How many agents?"
# Output: There are 3 agents in the system: test_agent, workflow_agent, bulk_agent
```

### **Get the best performer:**
```bash
python3 agent_inquiry.py "Who is the best agent?"
# Output: 🏆 workflow_agent (100.0% completion rate)
```

### **Check specific agent:**
```bash
python3 agent_inquiry.py "Tell me about test_agent" --agent test_agent
# Output: Detailed stats for test_agent
```

### **Overall dashboard:**
```bash
python3 agent_inquiry.py "Show me the dashboard"
# Output: Complete statistics for all agents
```

---

## 🎯 **Pro Tips**

1. **Use natural language** - The inquiry tool understands conversational questions
2. **Be specific** - Ask about particular agents by name for detailed info
3. **Use time periods** - Add `--days 30` for longer historical analysis
4. **Interactive mode** - Great for exploring and asking follow-up questions
5. **Combine with CLI** - Use CLI commands for automation and scripting

Your MCP client now supports full agent management and inquiry! 🎉