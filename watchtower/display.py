"""
Terminal Display — What the developer actually sees.

Clean, colored output that makes loops impossible to miss.
"""

from .loop_score import LoopResult, Step

# ANSI color codes
GRAY = "\033[90m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CYAN = "\033[96m"
WHITE = "\033[97m"


def format_step(step: Step, result: LoopResult) -> str:
    """Format a single step for terminal output."""

    step_num = f"{DIM}[watchtower]{RESET} "
    step_num += f"{GRAY}step {step.step_number:>2}{RESET}"

    # Node name
    node = f" {CYAN}{step.node_name}{RESET}"

    # Tool calls OR action label
    action = ""
    if step.tool_calls:
        tool_str = ", ".join(step.tool_calls[:2])
        if len(step.tool_calls) > 2:
            tool_str += f" +{len(step.tool_calls) - 2}"
        action = f" → {WHITE}{tool_str}{RESET}"
    elif step.action_label:
        action = f" → {DIM}{step.action_label}{RESET}"

    # Status indicator
    if result.score < 0.3:
        status = f" {GREEN}✓{RESET}"
    elif result.score < 0.5:
        status = f" {YELLOW}~{RESET} {DIM}score:{result.score}{RESET}"
    elif result.score < 0.7:
        status = f" {YELLOW}⚡ repeat{RESET} {DIM}score:{result.score}{RESET}"
    else:
        status = f" {RED}⚡ repeat{RESET} {DIM}score:{result.score}{RESET}"

    return f"{step_num}{node}{action}{status}"


def format_alert(result: LoopResult, detected_at_step: int) -> str:
    """Format the ONE hero alert — dramatic, informative, with ROI."""
    lines = []
    lines.append("")
    lines.append(f"  {RED}{BOLD}⚠️  LOOP DETECTED{RESET}")
    lines.append(f"  {RED}{'─' * 50}{RESET}")
    lines.append(f"  {WHITE}Score:     {BOLD}{result.score}{RESET}  {'🔴' if result.score >= 0.8 else '🟡'}")
    lines.append(f"  {WHITE}Pattern:   {BOLD}{result.pattern}{RESET}  (×{result.repeat_count})")
    lines.append(f"  {GRAY}Breakdown: node_rep={result.node_repetition}  seq_rep={result.sequence_repetition}  tool_rep={result.tool_repetition}{RESET}")
    lines.append(f"  {RED}{'─' * 50}{RESET}")
    lines.append(f"  {YELLOW}⏱  Caught at step {detected_at_step} — without detection this loop would continue indefinitely.{RESET}")
    lines.append("")
    return "\n".join(lines)


def format_summary(total_steps: int, alerts: int, max_score: float) -> str:
    """Format end-of-run summary."""
    lines = []
    lines.append("")
    lines.append(f"  {DIM}{'─' * 50}{RESET}")
    lines.append(f"  {BOLD}watchtower summary{RESET}")
    lines.append(f"  {GRAY}Steps monitored:  {WHITE}{total_steps}{RESET}")
    lines.append(f"  {GRAY}Loop detected:    {RED + 'yes' if alerts > 0 else GREEN + 'no'}{RESET}")
    lines.append(f"  {GRAY}Peak loop score:  {RED if max_score >= 0.7 else GREEN}{max_score}{RESET}")
    lines.append(f"  {DIM}{'─' * 50}{RESET}")
    lines.append("")
    return "\n".join(lines)


def format_start(framework: str) -> str:
    """Format the startup banner."""
    lines = []
    lines.append("")
    lines.append(f"  {DIM}{'─' * 50}{RESET}")
    lines.append(f"  {BOLD}🗼 watchtower{RESET} {DIM}v0.1.0{RESET}")
    lines.append(f"  {GRAY}monitoring: {WHITE}{framework}{RESET}")
    lines.append(f"  {GRAY}metrics:    {WHITE}Loop Score{RESET}")
    lines.append(f"  {DIM}{'─' * 50}{RESET}")
    lines.append("")
    return "\n".join(lines)
