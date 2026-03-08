from __future__ import annotations

from typing import Any, Literal, Mapping, TypedDict, cast

WorldRole = Literal["truman", "cast", "npc"]


class DirectorGuidance(TypedDict, total=False):
    director_scene_goal: str
    director_priority: str
    director_message_hint: str
    director_target_agent_id: str
    director_location_hint: str
    director_reason: str


class ScenarioAgentProfile(TypedDict, total=False):
    bio: str
    agent_config_id: str
    world_role: WorldRole
    workplace: str
    workplace_location_id: str
    work_description: str
    director_scene_goal: str
    director_priority: str
    director_message_hint: str
    director_target_agent_id: str
    director_location_hint: str
    director_reason: str


def get_world_role(profile: Mapping[str, Any] | None) -> WorldRole | None:
    if not profile:
        return None
    world_role = profile.get("world_role")
    if world_role in {"truman", "cast", "npc"}:
        return cast(WorldRole, world_role)
    return None


def get_agent_config_id(profile: Mapping[str, Any] | None) -> str | None:
    if not profile:
        return None
    agent_config_id = profile.get("agent_config_id")
    return agent_config_id if isinstance(agent_config_id, str) and agent_config_id else None


def build_director_guidance(
    *,
    scene_goal: str | None,
    priority: str | None,
    message_hint: str | None,
    target_agent_id: str | None,
    location_hint: str | None,
    reason: str | None,
) -> DirectorGuidance:
    guidance: DirectorGuidance = {}
    if scene_goal is None:
        return guidance

    guidance["director_scene_goal"] = scene_goal
    if priority is not None:
        guidance["director_priority"] = priority
    if message_hint is not None:
        guidance["director_message_hint"] = message_hint
    if target_agent_id is not None:
        guidance["director_target_agent_id"] = target_agent_id
    if location_hint is not None:
        guidance["director_location_hint"] = location_hint
    if reason is not None:
        guidance["director_reason"] = reason
    return guidance


def build_scenario_agent_profile(
    *,
    agent_config_id: str | None = None,
    world_role: WorldRole | None = None,
    bio: str | None = None,
    workplace: str | None = None,
    workplace_location_id: str | None = None,
    work_description: str | None = None,
    guidance: DirectorGuidance | None = None,
    extras: Mapping[str, Any] | None = None,
) -> ScenarioAgentProfile:
    profile = cast(ScenarioAgentProfile, dict(extras or {}))
    if bio is not None:
        profile["bio"] = bio
    if agent_config_id is not None:
        profile["agent_config_id"] = agent_config_id
    if world_role is not None:
        profile["world_role"] = world_role
    if workplace is not None:
        profile["workplace"] = workplace
    if workplace_location_id is not None:
        profile["workplace_location_id"] = workplace_location_id
    if work_description is not None:
        profile["work_description"] = work_description
    if guidance:
        profile.update(guidance)
    return profile


def get_director_guidance(profile: Mapping[str, Any] | None) -> DirectorGuidance:
    if not profile:
        return {}
    return build_director_guidance(
        scene_goal=_as_optional_str(profile.get("director_scene_goal")),
        priority=_as_optional_str(profile.get("director_priority")),
        message_hint=_as_optional_str(profile.get("director_message_hint")),
        target_agent_id=_as_optional_str(profile.get("director_target_agent_id")),
        location_hint=_as_optional_str(profile.get("director_location_hint")),
        reason=_as_optional_str(profile.get("director_reason")),
    )


def merge_scenario_agent_profile(
    profile: Mapping[str, Any] | None,
    guidance: DirectorGuidance | None = None,
) -> ScenarioAgentProfile:
    return build_scenario_agent_profile(guidance=guidance, extras=profile)


def _as_optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None
