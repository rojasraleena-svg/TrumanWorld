"""World rules for TrumanWorld scenario.

This module defines the cognitive rules for how agents perceive each other
and infer information from observations. These rules are scenario-specific
and should be injected at the scenario layer.

认知规则设计原则：
1. 可观察性分级：外表 > 行为 > 推断信息
2. 场景上下文：同一行为在不同场所有不同含义
3. 数据驱动：规则配置化，便于扩展
"""

from __future__ import annotations

from typing import Any


# =============================================================================
# 职业外观映射：定义不同职业的可观察特征
# =============================================================================

OCCUPATION_APPEARANCE: dict[str, dict[str, str]] = {
    "insurance clerk": {
        "appearance": "穿着正装",
        "typical_activity": "处理文件",
        "typical_location": "办公室",
    },
    "hospital staff": {
        "appearance": "穿着便装，可能刚下班",
        "typical_activity": "通勤或休息",
        "typical_location": "医院或家中",
    },
    "office coworker": {
        "appearance": "穿着正装",
        "typical_activity": "处理文件",
        "typical_location": "办公室",
    },
    "barista": {
        "appearance": "穿着围裙",
        "typical_activity": "制作咖啡",
        "typical_location": "咖啡馆",
    },
    "shop regular": {
        "appearance": "穿着休闲",
        "typical_activity": "喝咖啡或看书",
        "typical_location": "公共空间",
    },
    "resident": {
        "appearance": "穿着休闲",
        "typical_activity": "日常活动",
        "typical_location": "小镇各处",
    },
}


# =============================================================================
# 场所类型推断规则
# =============================================================================

LOCATION_TYPE_RULES: dict[str, dict[str, str]] = {
    "cafe": {
        "context": "咖啡馆",
        "typical_workers": ["barista"],
        "typical_visitors": ["resident", "shop regular", "office coworker"],
        "activity_hint_customer": "坐在座位上喝咖啡",
        "activity_hint_worker": "在咖啡机后面忙碌",
    },
    "office": {
        "context": "办公室",
        "typical_workers": ["insurance clerk", "office coworker"],
        "typical_visitors": [],
        "activity_hint": "在工位上工作",
    },
    "home": {
        "context": "住宅",
        "typical_workers": [],
        "typical_visitors": [],
        "activity_hint": "在家休息",
    },
    "plaza": {
        "context": "广场",
        "typical_workers": [],
        "typical_visitors": ["resident", "shop regular"],
        "activity_hint": "在广场散步或闲逛",
    },
}


# =============================================================================
# 关系熟悉度等级
# =============================================================================

RELATIONSHIP_LEVELS = {
    "family": {
        "min_familiarity": 0.9,
        "knowledge_level": "full",  # 知道职业、工作地点、性格等
        "description": "家人，完全了解对方信息",
    },
    "close_friend": {
        "min_familiarity": 0.7,
        "knowledge_level": "high",  # 知道职业、工作地点
        "description": "密友，较了解对方信息",
    },
    "friend": {
        "min_familiarity": 0.5,
        "knowledge_level": "medium",  # 知道职业
        "description": "朋友，知道基本情况",
    },
    "acquaintance": {
        "min_familiarity": 0.3,
        "knowledge_level": "low",  # 知道名字，面熟
        "description": "熟人，点头之交",
    },
    "stranger": {
        "min_familiarity": 0.0,
        "knowledge_level": "none",  # 需要通过观察推断
        "description": "陌生人，仅能通过观察推断",
    },
}


# =============================================================================
# 核心函数：构建可观察线索
# =============================================================================


def build_observable_cues(
    occupation: str | None,
    location_type: str | None,
    is_at_workplace: bool = False,
) -> dict[str, Any]:
    """构建角色的可观察线索。

    Args:
        occupation: 角色职业
        location_type: 当前地点类型
        is_at_workplace: 是否在工作地点

    Returns:
        包含可观察线索的字典
    """
    cues: dict[str, Any] = {}

    if not occupation or occupation not in OCCUPATION_APPEARANCE:
        return cues

    occupation_info = OCCUPATION_APPEARANCE[occupation]
    cues["appearance"] = occupation_info["appearance"]
    cues["typical_activity"] = occupation_info["typical_activity"]

    # 根据地点和职业推断当前行为
    if location_type and location_type in LOCATION_TYPE_RULES:
        location_info = LOCATION_TYPE_RULES[location_type]

        # 如果在工作地点，显示工作行为
        if is_at_workplace:
            if location_type == "cafe" and occupation in location_info.get("typical_workers", []):
                cues["current_activity_hint"] = location_info.get("activity_hint_worker", "在工作")
            elif location_type == "office":
                cues["current_activity_hint"] = location_info.get("activity_hint", "在工作")
        else:
            # 不在工作地点，显示访客行为
            if location_type == "cafe":
                cues["current_activity_hint"] = location_info.get("activity_hint_customer", "喝咖啡")
            elif location_type == "plaza":
                cues["current_activity_hint"] = location_info.get("activity_hint", "闲逛")
            elif location_type == "home":
                cues["current_activity_hint"] = location_info.get("activity_hint", "休息")

    return cues


def infer_knowledge_from_relationship(
    familiarity: float,
    other_occupation: str | None,
    other_workplace: str | None,
) -> dict[str, Any]:
    """根据关系熟悉度推断对对方的了解程度。

    Args:
        familiarity: 熟悉度 (0.0 - 1.0)
        other_occupation: 对方职业
        other_workplace: 对方工作地点

    Returns:
        可推断的知识信息
    """
    knowledge: dict[str, Any] = {"knowledge_level": "none"}

    # 确定关系等级
    for level, info in RELATIONSHIP_LEVELS.items():
        if familiarity >= info["min_familiarity"]:
            knowledge["relationship_level"] = level
            knowledge["knowledge_level"] = info["knowledge_level"]
            knowledge["description"] = info["description"]
            break

    # 根据知识等级返回可推断的信息
    knowledge_level = knowledge.get("knowledge_level", "none")

    if knowledge_level in ("full", "high"):
        # 完全了解或较高了解：知道职业和工作地点
        knowledge["known_occupation"] = other_occupation
        knowledge["known_workplace"] = other_workplace
    elif knowledge_level == "medium":
        # 中等了解：知道职业
        knowledge["known_occupation"] = other_occupation
    elif knowledge_level == "low":
        # 较低了解：仅知道是熟人
        knowledge["is_acquaintance"] = True
    else:
        # 陌生人：需要通过观察推断
        knowledge["requires_observation"] = True

    return knowledge


def build_perception_context(
    viewer_id: str,
    nearby_agents: list[dict[str, Any]],
    relationships: dict[str, float],  # agent_id -> familiarity
    current_location_type: str | None,
) -> dict[str, Any]:
    """构建感知上下文，注入到 agent 的决策上下文中。

    Args:
        viewer_id: 观察者 ID
        nearby_agents: 附近的 agent 列表，每个包含 id, name, occupation, workplace_id, is_at_workplace
        relationships: 与各 agent 的熟悉度映射
        current_location_type: 当前地点类型

    Returns:
        感知上下文字典
    """
    perceived_agents = []

    for agent in nearby_agents:
        if agent.get("id") == viewer_id:
            continue

        agent_id = agent.get("id", "")
        familiarity = relationships.get(agent_id, 0.0)

        # 获取可观察线索
        observable = build_observable_cues(
            occupation=agent.get("occupation"),
            location_type=current_location_type,
            is_at_workplace=agent.get("is_at_workplace", False),
        )

        # 获取基于关系的知识
        knowledge = infer_knowledge_from_relationship(
            familiarity=familiarity,
            other_occupation=agent.get("occupation"),
            other_workplace=agent.get("workplace_id"),
        )

        perceived = {
            "id": agent_id,
            "name": agent.get("name"),
            "familiarity": familiarity,
            "relationship_level": knowledge.get("relationship_level", "stranger"),
            "observable_cues": observable,
        }

        # 根据熟悉度决定是否提供已知信息
        if knowledge.get("known_occupation"):
            perceived["known_occupation"] = knowledge["known_occupation"]
        if knowledge.get("known_workplace"):
            perceived["known_workplace"] = knowledge["known_workplace"]

        perceived_agents.append(perceived)

    return {
        "perceived_others": perceived_agents,
        "perception_rules": {
            "观察优先": "先看外表和行为，再结合已知信息",
            "推断限制": "不熟悉的陌生人只能通过场景推断职业",
            "记忆整合": "已知的熟人信息来自长期记忆",
        },
    }
