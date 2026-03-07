from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class LocationState:
    id: str
    name: str
    capacity: int = 10
    occupants: set[str] = field(default_factory=set)


@dataclass
class AgentState:
    id: str
    name: str
    location_id: str
    status: dict[str, Any] = field(default_factory=dict)


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
                }
                for location_id, location in self.locations.items()
            },
            "agents": {
                agent_id: {
                    "name": agent.name,
                    "location_id": agent.location_id,
                    "status": deepcopy(agent.status),
                }
                for agent_id, agent in self.agents.items()
            },
        }

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
