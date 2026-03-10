from __future__ import annotations

from typing import TYPE_CHECKING

from app.infra.logging import get_logger
from app.sim.day_boundary import (
    run_evening_reflection,
    run_morning_planning,
    should_run_planner,
    should_run_reflector,
)
from app.sim.event_utils import build_event
from app.sim.persistence import PersistenceManager

if TYPE_CHECKING:
    from app.scenario.base import Scenario
    from app.sim.runner import TickResult
    from app.sim.world import WorldState
    from app.store.models import Event, LlmCall
    from sqlalchemy.ext.asyncio import AsyncSession


logger = get_logger(__name__)


class TickPersistenceService:
    def __init__(self, session: "AsyncSession | None" = None) -> None:
        self.session = session
        self.persistence = PersistenceManager(session) if session is not None else None

    async def persist_tick_events(
        self,
        *,
        run_id: str,
        result: "TickResult",
        scenario: "Scenario",
    ) -> list["Event"]:
        if self.persistence is None:
            msg = "TickPersistenceService.persist_tick_events requires a bound session"
            raise RuntimeError(msg)

        events = [
            build_event(
                run_id=run_id,
                tick_no=result.tick_no,
                world_time=result.world_time,
                action_type=item.action_type,
                payload=item.event_payload,
                accepted=True,
            )
            for item in result.accepted
        ]
        events.extend(
            build_event(
                run_id=run_id,
                tick_no=result.tick_no,
                world_time=result.world_time,
                action_type=item.action_type,
                payload={"reason": item.reason, **item.event_payload},
                accepted=False,
            )
            for item in result.rejected
        )
        if not events:
            return []

        persisted = await self.persistence.event_repo.create_many(events)
        await self.persistence.persist_tick_memories(run_id, persisted)
        await self.persistence.persist_tick_relationships(run_id, persisted)
        await scenario.update_state_from_events(run_id, persisted)
        return persisted

    async def persist_isolated_tick(
        self,
        *,
        run_id: str,
        current_tick: int,
        result: "TickResult",
        world: "WorldState",
        scenario: "Scenario",
        director_plan,
        llm_records: list["LlmCall"],
        engine,
        agent_runtime,
    ) -> None:
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine, expire_on_commit=False) as write_session:
            persistence = PersistenceManager(write_session)
            persisted_events = await persistence.persist_tick_results(
                run_id, result, world, current_tick + 1
            )
            write_scenario = scenario.with_session(write_session)
            await write_scenario.update_state_from_events(run_id, persisted_events)
            if director_plan is not None:
                try:
                    await write_scenario.persist_director_plan(run_id, director_plan)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Failed to persist director plan for run {run_id}: {exc}")

        await self.persist_llm_records(run_id=run_id, llm_records=llm_records, engine=engine)
        await self.run_day_boundary_tasks(
            run_id=run_id,
            result=result,
            world=world,
            engine=engine,
            agent_runtime=agent_runtime,
        )

    async def persist_llm_records(
        self, *, run_id: str, llm_records: list["LlmCall"], engine
    ) -> None:
        if not llm_records or engine is None:
            return

        from sqlalchemy.ext.asyncio import AsyncSession

        try:
            async with AsyncSession(engine, expire_on_commit=False) as llm_session:
                for record in llm_records:
                    llm_session.add(record)
                await llm_session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to persist llm_calls for run {run_id}: {exc}")

    async def run_day_boundary_tasks(
        self,
        *,
        run_id: str,
        result: "TickResult",
        world: "WorldState",
        engine,
        agent_runtime,
    ) -> None:
        if engine is None:
            return

        try:
            if should_run_planner(world):
                await run_morning_planning(
                    run_id=run_id,
                    tick_no=result.tick_no,
                    world=world,
                    engine=engine,
                    agent_runtime=agent_runtime,
                )
            elif should_run_reflector(world):
                await run_evening_reflection(
                    run_id=run_id,
                    tick_no=result.tick_no,
                    world=world,
                    engine=engine,
                    agent_runtime=agent_runtime,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Day boundary task failed: {exc}")
