from __future__ import annotations

from app.agent.providers import RuntimeDecision
from app.protocol.simulation import (
    ACTION_MOVE,
    ACTION_TALK,
    DIRECTOR_SCENE_KEEP_NATURAL,
    DIRECTOR_SCENE_SOFT_CHECK_IN,
)
from app.scenario.truman_world.types import get_director_guidance
from app.sim.types import RuntimeWorldContext


def build_truman_world_decision(
    *,
    world: RuntimeWorldContext,
    nearby_agent_id: str | None,
    current_location_id: str | None,
    home_location_id: str | None,
) -> RuntimeDecision | None:
    suspicion_decision = _build_suspicion_aware_decision(
        world=world,
        nearby_agent_id=nearby_agent_id,
        current_location_id=current_location_id,
        home_location_id=home_location_id,
    )
    if suspicion_decision is not None:
        return suspicion_decision

    return _build_cast_stabilizing_decision(
        world=world,
        nearby_agent_id=nearby_agent_id,
    )


def _build_suspicion_aware_decision(
    *,
    world: RuntimeWorldContext,
    nearby_agent_id: str | None,
    current_location_id: str | None,
    home_location_id: str | None,
) -> RuntimeDecision | None:
    world_role = world.get("world_role")
    self_status = world.get("self_status", {}) or {}
    suspicion_score = float(self_status.get("suspicion_score", 0.0) or 0.0)

    if world_role != "truman":
        return None

    if suspicion_score >= 0.9 and home_location_id and current_location_id != home_location_id:
        return RuntimeDecision(action_type=ACTION_MOVE, target_location_id=str(home_location_id))

    if suspicion_score >= 0.75 and nearby_agent_id:
        return RuntimeDecision(
            action_type=ACTION_TALK,
            target_agent_id=str(nearby_agent_id),
            message="今天总有点怪怪的，你刚刚有注意到什么吗？",
        )

    return None


def _build_cast_stabilizing_decision(
    *,
    world: RuntimeWorldContext,
    nearby_agent_id: str | None,
) -> RuntimeDecision | None:
    world_role = world.get("world_role")
    truman_suspicion_score = float(world.get("truman_suspicion_score", 0.0) or 0.0)
    guidance = get_director_guidance(world)
    scene_goal = guidance.get("director_scene_goal")
    guidance_priority = guidance.get("director_priority")

    if world_role != "cast":
        return None

    if scene_goal not in {DIRECTOR_SCENE_SOFT_CHECK_IN, DIRECTOR_SCENE_KEEP_NATURAL}:
        return None

    if nearby_agent_id and truman_suspicion_score >= 0.8:
        return RuntimeDecision(
            action_type=ACTION_TALK,
            target_agent_id=str(nearby_agent_id),
            message=("我刚刚也在忙日常那些事，可能只是节奏有点乱。要不要先顺着手头的安排慢慢来？"),
            payload={"guidance_priority": guidance_priority or "advisory"},
        )

    return None
