from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.scenario.base import Scenario
from app.scenario.adapter_registry import get_scenario_adapter_registry
from app.scenario.bundle_registry import get_scenario_bundle_registry


def create_scenario(
    scenario_type: str | None,
    session: AsyncSession | None = None,
) -> Scenario:
    bundle = get_scenario_bundle_registry().get_bundle(scenario_type)
    adapter_registry = get_scenario_adapter_registry()
    adapter = bundle.manifest.adapter if bundle is not None else "truman_world"
    scenario_id = bundle.manifest.id if bundle is not None else "truman_world"
    return adapter_registry.build(adapter, scenario_id=scenario_id, session=session)
