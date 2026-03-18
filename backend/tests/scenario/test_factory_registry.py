from __future__ import annotations

import pytest

from app.infra.settings import get_settings
from app.scenario.factory import create_scenario
from app.scenario.open_world.scenario import OpenWorldScenario
from app.scenario.truman_world.scenario import TrumanWorldScenario


def test_factory_resolves_runtime_adapter_from_bundle_registry(tmp_path, monkeypatch: pytest.MonkeyPatch):
    scenarios_root = tmp_path / "scenarios"
    truman_root = scenarios_root / "truman_world"
    truman_root.mkdir(parents=True)
    (truman_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: truman_world",
                "name: Truman World",
                "version: 1",
                "runtime_adapter: truman_world",
            ]
        ),
        encoding="utf-8",
    )
    open_world_root = scenarios_root / "open_world"
    open_world_root.mkdir(parents=True)
    (open_world_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: open_world",
                "name: Open World",
                "version: 1",
                "runtime_adapter: open_world",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    open_world = create_scenario("open_world")
    truman_world = create_scenario("truman_world")

    assert isinstance(open_world, OpenWorldScenario)
    assert isinstance(truman_world, TrumanWorldScenario)


def test_factory_falls_back_to_truman_world_when_bundle_missing(tmp_path, monkeypatch: pytest.MonkeyPatch):
    scenarios_root = tmp_path / "scenarios"
    truman_root = scenarios_root / "truman_world"
    truman_root.mkdir(parents=True)
    (truman_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: truman_world",
                "name: Truman World",
                "version: 1",
                "runtime_adapter: truman_world",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    scenario = create_scenario("unknown_world")

    assert isinstance(scenario, TrumanWorldScenario)
