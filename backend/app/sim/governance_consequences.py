from __future__ import annotations

from app.sim.action_resolver import ActionResult
from app.sim.world import WorldState

WARN_ATTENTION_DELTA = 0.05
BLOCK_ATTENTION_DELTA = 0.15
MAX_ATTENTION_SCORE = 1.0


def apply_governance_consequences(world: WorldState, result: ActionResult) -> None:
    governance_execution = result.governance_execution
    if governance_execution is None:
        return
    if governance_execution.decision not in {"warn", "block"}:
        return

    agent_id = result.event_payload.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return

    agent = world.get_agent(agent_id)
    if agent is None:
        return

    status = dict(agent.status or {})
    status["warning_count"] = int(status.get("warning_count", 0) or 0) + 1

    current_attention = float(status.get("governance_attention_score", 0.0) or 0.0)
    delta = (
        WARN_ATTENTION_DELTA
        if governance_execution.decision == "warn"
        else BLOCK_ATTENTION_DELTA
    )
    status["governance_attention_score"] = min(MAX_ATTENTION_SCORE, current_attention + delta)
    agent.status = status
