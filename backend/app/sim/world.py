from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# 职业外观映射：定义不同职业的可观察特征
OCCUPATION_APPEARANCE = {
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


@dataclass
class LocationState:
    id: str
    name: str
    capacity: int = 10
    occupants: set[str] = field(default_factory=set)
    location_type: str | None = None  # 新增：地点类型


@dataclass
class AgentState:
    id: str
    name: str
    location_id: str
    status: dict[str, Any] = field(default_factory=dict)
    occupation: str | None = None  # 新增：职业
    workplace_id: str | None = None  # 新增：工作地点 ID

    def get_observable_cues(self, location_type: str | None = None) -> dict[str, Any]:
        """返回可观察的行为线索，基于职业和当前场景推断"""
        cues = {}

        # 获取职业对应的外观特征
        if self.occupation and self.occupation in OCCUPATION_APPEARANCE:
            occupation_cues = OCCUPATION_APPEARANCE[self.occupation]
            cues["appearance"] = occupation_cues["appearance"]
            cues["typical_activity"] = occupation_cues["typical_activity"]

            # 根据当前地点调整行为推断
            if location_type == "cafe":
                if self.occupation == "barista":
                    cues["current_activity_hint"] = "在咖啡机后面忙碌"
                else:
                    cues["current_activity_hint"] = "坐在座位上"
            elif location_type == "office":
                cues["current_activity_hint"] = "在工位上工作"
            elif location_type == "home":
                cues["current_activity_hint"] = "在家休息"
            elif location_type == "plaza":
                cues["current_activity_hint"] = "在广场散步或闲逛"

        return cues


class WorldState:
    """Authoritative in-memory world state facade."""

    def __init__(
        self,
        current_time: datetime,
        tick_minutes: int = 5,
        locations: dict[str, LocationState] | None = None,
        agents: dict[str, AgentState] | None = None,
    ) -> None:
        self.current_time = current_time
        self.tick_minutes = tick_minutes
        self.locations = locations or {}
        self.agents = agents or {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "current_time": self.current_time.isoformat(),
            "tick_minutes": self.tick_minutes,
            "clock": self.time_context(),
            "locations": {
                location_id: {
                    "name": location.name,
                    "capacity": location.capacity,
                    "occupants": sorted(location.occupants),
                    "location_type": location.location_type,
                }
                for location_id, location in self.locations.items()
            },
            "agents": {
                agent_id: {
                    "name": agent.name,
                    "location_id": agent.location_id,
                    "status": deepcopy(agent.status),
                    "occupation": agent.occupation,
                    "workplace_id": agent.workplace_id,
                }
                for agent_id, agent in self.agents.items()
            },
        }

    def get_observable_agents_at_location(self, location_id: str) -> list[dict[str, Any]]:
        """获取某地点所有 agent 的可观察信息"""
        location = self.locations.get(location_id)
        if location is None:
            return []

        result = []
        for agent_id in location.occupants:
            agent = self.agents.get(agent_id)
            if agent is None:
                continue

            observable = {
                "id": agent.id,
                "name": agent.name,
                "observable_cues": agent.get_observable_cues(location.location_type),
            }
            result.append(observable)

        return result

    def time_context(self) -> dict[str, Any]:
        weekday = self.current_time.weekday()
        minute_of_day = (self.current_time.hour * 60) + self.current_time.minute
        return {
            "current_time": self.current_time.isoformat(),
            "tick_minutes": self.tick_minutes,
            "day_index": self._day_index(),
            "weekday": weekday,
            "weekday_name": self._weekday_name(weekday),
            "hour": self.current_time.hour,
            "minute": self.current_time.minute,
            "minute_of_day": minute_of_day,
            "is_weekend": weekday >= 5,
            "time_period": self._time_period(),
        }

    def advance_tick(self) -> datetime:
        self.current_time = self.current_time + timedelta(minutes=self.tick_minutes)
        return self.current_time

    def get_agent(self, agent_id: str) -> AgentState | None:
        return self.agents.get(agent_id)

    def get_location(self, location_id: str) -> LocationState | None:
        return self.locations.get(location_id)

    def move_agent(self, agent_id: str, destination_id: str) -> None:
        agent = self.agents[agent_id]
        origin = self.locations[agent.location_id]
        destination = self.locations[destination_id]

        origin.occupants.discard(agent_id)
        destination.occupants.add(agent_id)
        agent.location_id = destination_id

    def _day_index(self) -> int:
        return self.current_time.toordinal()

    def _weekday_name(self, weekday: int) -> str:
        names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return names[weekday]

    def _time_period(self) -> str:
        hour = self.current_time.hour
        if hour < 6:
            return "night"
        if hour < 9:
            return "morning"
        if hour < 12:
            return "late_morning"
        if hour < 14:
            return "noon"
        if hour < 18:
            return "afternoon"
        if hour < 22:
            return "evening"
        return "night"
