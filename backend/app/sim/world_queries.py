from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.sim.world import AgentState, LocationState, WorldState


def get_location(world: WorldState, location_id: str | None) -> LocationState | None:
    if not location_id:
        return None
    return world.get_location(location_id)


def get_agent(world: WorldState, agent_id: str | None) -> AgentState | None:
    if not agent_id:
        return None
    return world.get_agent(agent_id)


def find_nearby_agent(world: WorldState, agent_id: str, location_id: str) -> str | None:
    location = get_location(world, location_id)
    if location is None:
        return None

    for occupant_id in sorted(location.occupants):
        if occupant_id != agent_id:
            return occupant_id
    return None


def find_recent_conversation_partner(
    world: WorldState,
    agent_id: str,
    location_id: str,
    recent_events: list[dict[str, Any]] | None = None,
) -> str | None:
    location = get_location(world, location_id)
    if location is None:
        return None

    candidate_ids = {
        occupant_id for occupant_id in location.occupants if occupant_id != agent_id
    }
    if not candidate_ids:
        return None

    for event in reversed(recent_events or []):
        if event.get("event_type") not in {
            "speech",
            "listen",
            "conversation_started",
            "conversation_joined",
        }:
            continue

        actor_agent_id = event.get("actor_agent_id")
        target_agent_id = event.get("target_agent_id")

        if actor_agent_id == agent_id and isinstance(target_agent_id, str) and target_agent_id in candidate_ids:
            return target_agent_id
        if target_agent_id == agent_id and isinstance(actor_agent_id, str) and actor_agent_id in candidate_ids:
            return actor_agent_id

        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        participant_ids = payload.get("participant_ids")
        if not isinstance(participant_ids, list) or agent_id not in participant_ids:
            continue
        speaker_agent_id = payload.get("speaker_agent_id")
        if (
            isinstance(speaker_agent_id, str)
            and speaker_agent_id != agent_id
            and speaker_agent_id in candidate_ids
        ):
            return speaker_agent_id

    return find_nearby_agent(world, agent_id, location_id)


def list_other_occupants(
    world: WorldState, viewer_agent_id: str, location_id: str | None
) -> list[str]:
    location = get_location(world, location_id)
    if location is None:
        return []
    return [agent_id for agent_id in sorted(location.occupants) if agent_id != viewer_agent_id]


def get_location_occupants(
    world: WorldState, location_id: str | None, exclude_agent_id: str | None = None
) -> list[dict[str, Any]]:
    """Get all agents at a location with their basic info.

    Args:
        world: World state
        location_id: Location ID
        exclude_agent_id: Optional agent ID to exclude from results

    Returns:
        List of agent info dicts with id, name, occupation, workplace_id, is_at_workplace
    """
    location = get_location(world, location_id)
    if location is None:
        return []

    occupants = []
    for agent_id in location.occupants:
        if agent_id == exclude_agent_id:
            continue
        agent = get_agent(world, agent_id)
        if agent is None:
            continue
        occupants.append(
            {
                "id": agent.id,
                "name": agent.name,
                "occupation": agent.occupation,
                "workplace_id": agent.workplace_id,
                "is_at_workplace": agent.workplace_id == location_id,
            }
        )
    return occupants


def build_familiarity_map(relationships: Iterable[Any]) -> dict[str, float]:
    return {
        relationship.other_agent_id: float(relationship.familiarity)
        for relationship in relationships
        if getattr(relationship, "other_agent_id", None) is not None
    }


def build_relationship_context_map(relationships: Iterable[Any]) -> dict[str, dict[str, Any]]:
    context_map: dict[str, dict[str, Any]] = {}
    for relationship in relationships:
        other_agent_id = getattr(relationship, "other_agent_id", None)
        if other_agent_id is None:
            continue
        context_map[other_agent_id] = {
            "familiarity": float(getattr(relationship, "familiarity", 0.0) or 0.0),
            "trust": float(getattr(relationship, "trust", 0.0) or 0.0),
            "affinity": float(getattr(relationship, "affinity", 0.0) or 0.0),
            "relation_type": getattr(relationship, "relation_type", None),
        }
    return context_map
