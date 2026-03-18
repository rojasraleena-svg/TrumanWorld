from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.scenario.base import Scenario
from app.scenario.bundle_registry import get_scenario_bundle_registry
from app.scenario.open_world.scenario import OpenWorldScenario
from app.scenario.truman_world.scenario import TrumanWorldScenario


def create_scenario(
    scenario_type: str | None,
    session: AsyncSession | None = None,
) -> Scenario:
    bundle = get_scenario_bundle_registry().get_bundle(scenario_type)
    runtime_adapter = bundle.manifest.runtime_adapter if bundle is not None else scenario_type

    if runtime_adapter == "open_world":
        return OpenWorldScenario(session)
    scenario_id = bundle.manifest.id if bundle is not None else "truman_world"
    return TrumanWorldScenario(session, scenario_id=scenario_id)
