from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from app.scenario.truman_world.types import DirectorGuidance, WorldRole
from app.scenario.truman_world.types import ScenarioAgentProfile


@dataclass
class AgentDecisionSnapshot:
    id: str
    current_goal: str | None
    current_location_id: str
    home_location_id: str | None
    profile: ScenarioAgentProfile
    recent_events: list[dict[str, Any]]


class NearbyAgentContext(TypedDict):
    id: str
    name: str
    occupation: str | None


class RuntimeWorldContext(DirectorGuidance, total=False):
    current_goal: str
    current_location_id: str
    current_location_name: str
    current_location_type: str
    known_location_ids: list[str]
    home_location_id: str
    nearby_agent_id: str
    nearby_agent: NearbyAgentContext
    self_status: dict[str, Any]
    truman_suspicion_score: float
    world_role: WorldRole
    tick_no: int
    tick_minutes: int
    world_time: str
