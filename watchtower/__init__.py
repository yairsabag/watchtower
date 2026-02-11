"""
Watchtower — Runtime intelligence for multi-agent teams.

Usage:
    from watchtower import watch
    graph = watch(your_langgraph)
    result = graph.invoke(your_input)

That's it. Watchtower monitors execution and alerts on loops.
"""

__version__ = "0.1.0"

from typing import Any, Callable, Optional
from .loop_score import LoopResult
from .interceptor import WatchtowerInterceptor, StopMonitoring


def watch(
    graph,
    threshold: float = 0.7,
    window_size: int = 10,
    on_loop: Optional[Callable[[LoopResult], Any]] = None,
    silent: bool = False,
) -> WatchtowerInterceptor:
    """
    Wrap a LangGraph compiled graph with Watchtower monitoring.
    
    Args:
        graph: A compiled LangGraph StateGraph.
        threshold: Loop Score threshold for alerts (0.0-1.0, default 0.7).
        window_size: Number of recent steps to analyze (default 10).
        on_loop: Optional callback fired when loop is detected.
                 Receives a LoopResult with score, pattern, and details.
        silent: If True, suppresses terminal output (callbacks still fire).
    
    Returns:
        A monitored graph with the same .invoke() interface.
    
    Example:
        from watchtower import watch
        
        # Basic usage
        graph = watch(my_graph)
        result = graph.invoke({"messages": [...]})
        
        # With callback
        def alert(result):
            print(f"Loop! Score: {result.score}")
        
        graph = watch(my_graph, on_loop=alert, threshold=0.8)
    """
    return WatchtowerInterceptor(
        graph=graph,
        threshold=threshold,
        window_size=window_size,
        on_loop=on_loop,
        silent=silent,
    )
