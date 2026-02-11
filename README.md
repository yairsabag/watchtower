# 🗼 Watchtower

**Runtime loop detection for multi-agent AI teams.**

Watchtower monitors your LangGraph multi-agent system in real-time and catches infinite loops before they burn through your token budget.

One line to integrate. Zero config. Works today.

## The Problem

Multi-agent systems fail silently. A research agent keeps searching because it's "never satisfied." An analysis agent keeps requesting more data. Two agents ping-pong forever. You don't notice until the bill arrives.

Existing observability tools (Langfuse, LangSmith, Helicone) track individual LLM calls — cost, latency, tokens. **None of them understand team dynamics.** They see trees, not the forest.

## The Solution

```python
from watchtower import watch

graph = watch(your_langgraph)       # ← one line
result = graph.invoke(your_input)   # ← same as before
```

Watchtower computes a **Loop Score** (0.0 → 1.0) in real-time from three signals:

| Signal | What it detects |
|--------|----------------|
| **Node Repetition** | Same agents running over and over |
| **Sequence Cycles** | Repeating patterns like A→B→A→B→A→B |
| **Tool Call Repeats** | Same tool called with same parameters |

When the score crosses a threshold — one alert, execution stops, money saved.

## Try It (30 seconds)

```bash
git clone https://github.com/yairsabag/watchtower.git
cd watchtower
pip install langgraph langchain-core
python -m demo.loop_demo
```

What you'll see:

```
🗼 watchtower v0.1.0
monitoring: LangGraph
metrics:    Loop Score

[watchtower] step  1 research_agent → web_search(query=AI agent market analysis) ✓
[watchtower] step  2 analysis_agent → analyze ✓
[watchtower] step  3 research_agent → web_search(query=AI agent market analysis) ~ score:0.34
[watchtower] step  4 analysis_agent → analyze ⚡ repeat score:0.77
[watchtower] step  5 research_agent → web_search(query=AI agent market analysis) ⚡ repeat score:0.74
[watchtower] step  6 analysis_agent → analyze ⚡ repeat score:0.81

  ⚠️  LOOP DETECTED
  ──────────────────────────────────────────────────
  Score:     0.81  🔴
  Pattern:   research_agent→analysis_agent  (×3)
  ──────────────────────────────────────────────────
  ⏱  Caught at step 6 — without detection this loop would continue indefinitely.

  watchtower summary
  Steps monitored:  6
  Loop detected:    yes
  Peak loop score:  0.81

  ✓ Watchtower caught the loop and stopped execution.
```

## Use on Your Own Graph

```python
from watchtower import watch

# Your existing code
graph = build_my_graph().compile()

# Add Watchtower
monitored = watch(graph)
result = monitored.invoke(my_input)
```

### Options

```python
# Adjust sensitivity
monitored = watch(graph, threshold=0.8)

# Stop execution on loop detection
from watchtower import watch, StopMonitoring

def on_loop(result):
    print(f"Loop! {result.pattern} (×{result.repeat_count})")
    raise StopMonitoring()

monitored = watch(graph, on_loop=on_loop)

# Silent mode — no terminal output, just callbacks
monitored = watch(graph, silent=True, on_loop=my_callback)

# Access results after run
print(monitored.total_steps)
print(monitored.max_score)
print(monitored.alerts)
```

## How It Works

Watchtower wraps your compiled LangGraph and listens to every node execution via `stream()`. It doesn't modify behavior — it only observes. On each step, it updates a sliding window and computes Loop Score from the three signals. If the score crosses the threshold and the pattern has repeated 3+ times across 5+ steps, it fires one alert.

No ML models. No embeddings. No external API calls. Pure pattern matching that adds near-zero overhead.

## Roadmap

- [x] Loop Score (node repetition + sequence cycles + tool call repeats)
- [ ] Tool Thrash Index (wasted tool calls that don't advance the task)
- [ ] CrewAI adapter
- [ ] AutoGen adapter
- [ ] Webhook / JSON export
- [ ] Dashboard

## License

MIT — use it however you want.

---

**Built because multi-agent teams deserve the same observability that infrastructure has had for decades.**
