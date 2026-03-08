from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.scenario.truman_world.rules import build_perception_context

if TYPE_CHECKING:
    from app.sim.world import WorldState
    from app.store.models import Relationship


def filter_world_for_role(world_role: str, world: dict[str, Any]) -> dict[str, Any]:
    if world_role == "truman":
        return {
            key: value
            for key, value in world.items()
            if not key.startswith("director_") and not key.startswith("cast_")
        }
    return dict(world)


def build_role_context(world_role: str, world: dict[str, Any]) -> dict[str, Any]:
    if world_role == "truman":
        return {
            "perspective": "subjective",
            "focus": "以普通居民的身份体验世界，只根据亲身经历理解周围发生的事",
            "current_suspicion_score": world.get("self_status", {}).get("suspicion_score", 0.0),
            "guidance": [
                "不要假设自己知道幕后信息",
                "优先依据眼前线索和熟悉的日常节奏做判断",
            ],
        }
    if world_role == "cast":
        return {
            "perspective": "supporting_cast",
            "focus": "优先保持自然、熟悉、不过分用力的日常互动",
            "guidance": [
                "优先做自然、连续、不会突然破坏日常节奏的动作",
                "场景提示只是软参考，不需要生硬执行",
                "如果信息不足，选择最稳妥、最像熟人日常的回应",
            ],
        }
    return {
        "perspective": "background",
        "focus": "保持低风险、背景化、自然的存在感",
        "guidance": ["优先做简单稳定的动作"],
    }


def build_scene_guidance(world_role: str, world: dict[str, Any]) -> dict[str, Any]:
    if world_role != "cast":
        return {}

    scene_goal = world.get("director_scene_goal")
    if not scene_goal:
        return {}

    return {
        "scene_goal": scene_goal,
        "priority": world.get("director_priority", "advisory"),
        "message_hint": world.get("director_message_hint"),
        "target_agent_id": world.get("director_target_agent_id"),
        "location_hint": world.get("director_location_hint"),
        "reason": world.get("director_reason"),
        "is_advisory": True,
    }


def build_perception_context_for_agent(
    viewer_agent_id: str,
    world: WorldState,
    relationships: list[Relationship],
    current_location_id: str | None,
) -> dict[str, Any]:
    """为 agent 构建感知上下文，包含对其他人的观察和已知信息。

    这是场景层的核心函数，将可观察线索和关系知识整合到上下文中。

    Args:
        viewer_agent_id: 观察者 agent 的 ID
        world: 当前世界状态
        relationships: 该 agent 的所有关系
        current_location_id: 当前地点 ID

    Returns:
        包含 perceived_others 的感知上下文字典
    """
    if not current_location_id:
        return {}

    # 获取当前地点信息
    location = world.get_location(current_location_id)
    if location is None:
        return {}

    # 获取同地点的其他 agent
    nearby_agent_ids = [aid for aid in location.occupants if aid != viewer_agent_id]
    if not nearby_agent_ids:
        return {"perceived_others": []}

    # 构建关系映射
    relationship_map = {r.other_agent_id: r.familiarity for r in relationships}

    # 收集附近 agent 的信息
    nearby_agents = []
    for agent_id in nearby_agent_ids:
        agent = world.get_agent(agent_id)
        if agent is None:
            continue

        # 判断是否在工作地点
        is_at_workplace = agent.workplace_id == current_location_id

        nearby_agents.append({
            "id": agent.id,
            "name": agent.name,
            "occupation": agent.occupation,
            "workplace_id": agent.workplace_id,
            "is_at_workplace": is_at_workplace,
        })

    # 使用规则构建感知上下文
    return build_perception_context(
        viewer_id=viewer_agent_id,
        nearby_agents=nearby_agents,
        relationships=relationship_map,
        current_location_type=location.location_type,
    )
