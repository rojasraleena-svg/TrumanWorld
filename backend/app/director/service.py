from __future__ import annotations

from typing import TYPE_CHECKING

from app.director.manual_planner import ManualDirectorPlanner
from app.protocol.simulation import build_director_event_type
from app.scenario.types import get_world_role
from app.sim.context import get_run_world_time
from app.sim.event_utils import build_event
from app.store.repositories import (
    AgentRepository,
    DirectorMemoryRepository,
    EventRepository,
    RunRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DirectorEventService:
    def __init__(self, session: "AsyncSession") -> None:
        self.run_repo = RunRepository(session)
        self.agent_repo = AgentRepository(session)
        self.director_memory_repo = DirectorMemoryRepository(session)
        self.event_repo = EventRepository(session)
        self.manual_planner = ManualDirectorPlanner()

    async def inject_event(
        self,
        *,
        run_id: str,
        event_type: str,
        payload: dict,
        location_id: str | None = None,
        importance: float = 0.5,
    ) -> None:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        agents = await self.agent_repo.list_for_run(run_id)
        truman = next(
            (agent for agent in agents if get_world_role(agent.profile) == "truman"), None
        )
        plan = self.manual_planner.build_plan_from_manual_event(
            event_type=event_type,
            payload=payload,
            location_id=location_id,
            agents=agents,
            truman_agent_id=truman.id if truman else None,
        )
        if plan is None:
            msg = f"Unsupported director event type: {event_type}"
            raise ValueError(msg)

        await self.director_memory_repo.create(
            run_id=run_id,
            tick_no=run.current_tick,
            scene_goal=plan.scene_goal,
            target_cast_ids=plan.target_cast_ids,
            priority=plan.priority,
            urgency=plan.urgency,
            message_hint=plan.message_hint,
            target_agent_id=plan.target_agent_id,
            reason=plan.reason,
            trigger_suspicion_score=0.0,
            trigger_continuity_risk="stable",
            cooldown_ticks=plan.cooldown_ticks,
            location_hint=plan.location_hint,
        )

        event = build_event(
            run_id=run_id,
            tick_no=run.current_tick,
            world_time=get_run_world_time(run).isoformat(),
            action_type=build_director_event_type(event_type),
            payload=payload,
            accepted=True,
        )
        event.location_id = location_id
        event.importance = importance
        event.visibility = "system"
        await self.event_repo.create(event)
