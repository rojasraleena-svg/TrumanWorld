from __future__ import annotations

from typing import TYPE_CHECKING

from app.infra.logging import get_logger
from app.sim.day_boundary import (
    run_evening_reflection,
    run_morning_planning,
    should_run_planner,
    should_run_reflector,
)

if TYPE_CHECKING:
    from app.agent.runtime import AgentRuntime
    from app.sim.runner import TickResult
    from app.sim.world import WorldState


logger = get_logger(__name__)


class DayBoundaryCoordinator:
    async def run(
        self,
        *,
        run_id: str,
        result: "TickResult",
        world: "WorldState",
        engine,
        agent_runtime: "AgentRuntime",
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
