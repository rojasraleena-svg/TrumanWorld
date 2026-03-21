"""Runtime-level world configuration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.infra.settings import get_settings
from app.scenario.bundle_registry import load_world_config_for_scenario, resolve_default_scenario_id

_WORLD_CONFIG_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


def load_world_config(
    scenario_id: str | None = None,
    *,
    force_reload: bool = False,
) -> dict[str, Any]:
    """Load world configuration for a scenario, falling back to the default bundle."""
    project_root = get_settings().project_root
    resolved_scenario_id = scenario_id or resolve_default_scenario_id(project_root=project_root)
    cache_key = _build_cache_key(project_root, resolved_scenario_id)
    if not force_reload and cache_key in _WORLD_CONFIG_CACHE:
        return _WORLD_CONFIG_CACHE[cache_key]

    config = load_world_config_for_scenario(resolved_scenario_id, project_root=project_root)
    default_scenario_id = resolve_default_scenario_id(project_root=project_root)
    if not config and resolved_scenario_id != default_scenario_id:
        config = load_world_config_for_scenario(default_scenario_id, project_root=project_root)

    _WORLD_CONFIG_CACHE[cache_key] = config
    return config


def build_world_common_knowledge(scenario_id: str | None = None) -> dict[str, Any]:
    """Build the shared world knowledge exposed to runtime consumers."""
    config = load_world_config(scenario_id)
    return {
        "daily_rhythm": config.get("daily_rhythm", {}),
        "location_purposes": config.get("location_purposes", {}),
        "social_norms": config.get("social_norms", []),
        "location_descriptions": config.get("location_descriptions", {}),
        "time_suggestions": config.get("time_suggestions", {}),
    }


def _build_cache_key(project_root: Path, scenario_id: str) -> tuple[str, str]:
    return (str(project_root.resolve()), scenario_id)
