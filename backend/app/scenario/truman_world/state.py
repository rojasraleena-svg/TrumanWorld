from __future__ import annotations

from typing import TYPE_CHECKING

from app.store.repositories import AgentRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.store.models import Event


class TrumanWorldStateUpdater:
    """Updates Truman-world specific state such as suspicion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.agent_repo = AgentRepository(session)

    async def persist_truman_suspicion(self, run_id: str, events: list[Event]) -> None:
        agents = await self.agent_repo.list_for_run(run_id)
        changed = False
        for agent in agents:
            if (agent.profile or {}).get("world_role") != "truman":
                continue
            delta = self.calculate_suspicion_delta(agent.id, events)
            if delta == 0.0:
                continue
            status = dict(agent.status or {})
            current = float(status.get("suspicion_score", 0.0))
            status["suspicion_score"] = max(0.0, min(1.0, round(current + delta, 4)))
            agent.status = status
            changed = True
        if changed:
            await self.session.commit()

    @staticmethod
    def calculate_suspicion_delta(agent_id: str, events: list[Event]) -> float:
        delta = 0.0
        for event in events:
            payload = event.payload or {}
            involved = event.actor_agent_id == agent_id or event.target_agent_id == agent_id
            if not involved and payload.get("agent_id") != agent_id:
                continue

            if event.event_type.endswith("_rejected"):
                delta += 0.12
            elif event.event_type.startswith("director_"):
                delta += 0.2
            elif event.event_type == "talk":
                delta -= 0.02
            elif event.event_type in {"rest", "work"}:
                delta -= 0.01
            elif event.event_type == "move":
                delta -= 0.005
        return delta
