"""
Watchtower Demo — Loop Detection in Action

A research agent + analysis agent enter an infinite loop.
Watchtower detects it and stops execution.

Run:  python -m demo.loop_demo
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict
from langgraph.graph import StateGraph, END
from watchtower import watch, StopMonitoring


# ─── State ───
class AgentState(TypedDict):
    task: str
    research_results: list[str]
    analysis: str
    needs_more_research: bool
    final_output: str
    iteration: int
    messages: list


# ─── Simulated Agents ───

def research_agent(state: AgentState) -> dict:
    """Simulates a research agent that searches for info."""
    iteration = state.get("iteration", 0)
    results = state.get("research_results", [])

    new_result = f"Research finding #{iteration + 1}: AI market data"
    results = results + [new_result]

    from langchain_core.messages import AIMessage
    tool_msg = AIMessage(
        content=f"Searching for more data on: {state['task']}",
        tool_calls=[{
            "name": "web_search",
            "args": {"query": "AI agent market analysis"},
            "id": f"call_{iteration}",
        }]
    )

    return {
        "research_results": results,
        "iteration": iteration + 1,
        "messages": [tool_msg],
    }


def analysis_agent(state: AgentState) -> dict:
    """
    The buggy agent: ALWAYS requests more research.
    
    This is the most common multi-agent failure mode —
    an agent that never feels like it has enough data.
    """
    iteration = state.get("iteration", 0)

    if iteration < 20:  # safety valve
        return {
            "analysis": f"Round {iteration}: Data insufficient. Need more research.",
            "needs_more_research": True,
        }
    else:
        return {
            "analysis": "Analysis complete.",
            "needs_more_research": False,
        }


def writer_agent(state: AgentState) -> dict:
    """Writes the final output. Only reached if analysis is done."""
    return {
        "final_output": f"Report based on {len(state.get('research_results', []))} findings."
    }


# ─── Graph ───

def should_continue(state: AgentState) -> str:
    if state.get("needs_more_research", False):
        return "research"
    return "write"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("research_agent", research_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("writer_agent", writer_agent)
    graph.set_entry_point("research_agent")
    graph.add_edge("research_agent", "analysis_agent")
    graph.add_conditional_edges("analysis_agent", should_continue, {
        "research": "research_agent",
        "write": "writer_agent",
    })
    graph.add_edge("writer_agent", END)
    return graph.compile()


# ─── Run ───

def main():
    print()
    print("  \033[1m🗼 Watchtower Demo: Loop Detection\033[0m")
    print("  \033[90mA research agent + analysis agent enter a loop.\033[0m")
    print("  \033[90mWatch Watchtower detect it and stop execution.\033[0m")
    print()

    graph = build_graph()

    # The callback: stop execution when loop is detected
    def on_loop(result):
        raise StopMonitoring()

    monitored = watch(graph, threshold=0.7, on_loop=on_loop)

    monitored.invoke({
        "task": "AI agent market analysis 2026",
        "research_results": [],
        "analysis": "",
        "needs_more_research": False,
        "final_output": "",
        "iteration": 0,
        "messages": [],
    })

    if monitored.alerts:
        print("  \033[92m✓ Watchtower caught the loop and stopped execution.\033[0m")
        print("  \033[90mWithout Watchtower, this would run until your token budget is gone.\033[0m")
    print()


if __name__ == "__main__":
    main()
