"""
LangGraph Interceptor — Hooks into graph execution without modifying behavior.

Uses LangGraph's event streaming to capture every node execution,
extract relevant data, feed it to Loop Detector, and print results.
"""

import json
from typing import Any, Callable, Optional

from .loop_score import LoopDetector, Step, LoopResult
from .display import format_step, format_alert, format_summary, format_start


class StopMonitoring(Exception):
    """Raised by on_loop callback to gracefully stop execution."""
    pass


class WatchtowerInterceptor:
    """
    Wraps a LangGraph compiled graph and monitors execution.
    
    Usage:
        from watchtower import watch
        monitored = watch(your_graph)
        result = monitored.invoke(your_input)
    """

    def __init__(
        self,
        graph,
        threshold: float = 0.7,
        window_size: int = 10,
        min_steps: int = 5,
        on_loop: Optional[Callable[[LoopResult], Any]] = None,
        silent: bool = False,
    ):
        self.graph = graph
        self.detector = LoopDetector(window_size=window_size, threshold=threshold)
        self.threshold = threshold
        self.min_steps = min_steps
        self.on_loop = on_loop
        self.silent = silent
        self.alerts: list[LoopResult] = []
        self.max_score = 0.0
        self.total_steps = 0
        self._hero_alert_fired = False

    def invoke(self, input_data: Any, config: Optional[dict] = None, **kwargs) -> Any:
        """
        Run the graph with monitoring.
        
        Streams events from LangGraph, intercepts each node execution,
        computes Loop Score, and prints to terminal.
        """
        if not self.silent:
            print(format_start("LangGraph"))

        self.detector.reset()
        self.alerts = []
        self.max_score = 0.0
        self.total_steps = 0
        self._hero_alert_fired = False

        final_result = None
        config = config or {}

        try:
            for event in self.graph.stream(input_data, config=config, stream_mode="updates", **kwargs):
                for node_name, node_output in event.items():
                    if node_name.startswith("__"):
                        continue

                    tool_calls = self._extract_tool_calls(node_output)
                    action_label = self._extract_action_label(node_output, tool_calls)

                    step = Step(
                        node_name=node_name,
                        tool_calls=tool_calls,
                        action_label=action_label,
                    )

                    result = self.detector.add_step(step)
                    self.total_steps += 1
                    self.max_score = max(self.max_score, result.score)

                    # Print step
                    if not self.silent:
                        print(format_step(step, result))

                    # Alert logic: ONE hero alert, requires min steps + repeat count
                    if (
                        result.is_alert
                        and not self._hero_alert_fired
                        and self.total_steps >= self.min_steps
                        and result.repeat_count >= 3
                    ):
                        self._hero_alert_fired = True
                        self.alerts.append(result)
                        if not self.silent:
                            print(format_alert(result, self.total_steps))
                        if self.on_loop:
                            self.on_loop(result)

                    final_result = node_output

        except StopMonitoring:
            # Graceful stop triggered by on_loop callback
            if not self.silent:
                print(format_summary(self.total_steps, len(self.alerts), self.max_score))
            return final_result
        except Exception as e:
            if not self.silent:
                print(f"\033[93m  [watchtower] monitoring error: {e}\033[0m")
            return self.graph.invoke(input_data, config=config, **kwargs)

        if not self.silent:
            print(format_summary(self.total_steps, len(self.alerts), self.max_score))

        return final_result

    def _extract_tool_calls(self, output: Any) -> list[str]:
        """Extract tool call signatures from node output."""
        calls = []
        if output is None:
            return calls

        if isinstance(output, dict):
            messages = output.get("messages", [])
            if not isinstance(messages, list):
                messages = [messages]

            for msg in messages:
                if hasattr(msg, "tool_calls"):
                    for tc in msg.tool_calls:
                        name = tc.get("name", "unknown") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                        args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                        args_str = self._compact_args(args)
                        calls.append(f"{name}({args_str})")

                elif hasattr(msg, "additional_kwargs"):
                    for tc in msg.additional_kwargs.get("tool_calls", []):
                        func = tc.get("function", {})
                        name = func.get("name", "unknown")
                        args_str = func.get("arguments", "")
                        calls.append(f"{name}({self._compact_args(args_str)})")

            actions = output.get("actions", [])
            if isinstance(actions, list):
                for action in actions:
                    if hasattr(action, "tool"):
                        calls.append(f"{action.tool}({self._compact_args(action.tool_input)})")

        return calls

    def _extract_action_label(self, output: Any, tool_calls: list[str]) -> str:
        """
        Extract a human-readable action label for display.
        If no tool calls, try to infer what the agent did.
        """
        if tool_calls:
            return ""  # tool calls will be shown instead

        if output is None:
            return "idle"

        if isinstance(output, dict):
            if "analysis" in output:
                return "analyze"
            if "final_output" in output:
                return "write"
            if "needs_more_research" in output:
                val = output["needs_more_research"]
                return "decide → more research" if val else "decide → done"

            messages = output.get("messages", [])
            if messages:
                return "respond"

            keys = [k for k in output.keys() if not k.startswith("_")]
            if keys:
                return f"update({', '.join(keys[:2])})"

        return "step"

    def _compact_args(self, args: Any) -> str:
        """Make tool arguments compact for display."""
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                return args[:40] + "..." if len(str(args)) > 40 else str(args)

        if isinstance(args, dict):
            parts = []
            for k, v in list(args.items())[:2]:
                v_str = str(v)
                if len(v_str) > 30:
                    v_str = v_str[:30] + "..."
                parts.append(f"{k}={v_str}")
            result = ", ".join(parts)
            if len(args) > 2:
                result += ", ..."
            return result

        return str(args)[:40]
