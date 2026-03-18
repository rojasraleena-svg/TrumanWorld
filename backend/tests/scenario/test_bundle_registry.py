from __future__ import annotations

import pytest

from app.infra.settings import get_settings
from app.scenario.bundle_registry import ScenarioBundleRegistry, resolve_agents_root_for_scenario


def test_bundle_registry_loads_scenarios_from_directory(tmp_path):
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

    registry = ScenarioBundleRegistry(scenarios_root)

    bundles = registry.list_bundles()

    assert [bundle.manifest.id for bundle in bundles] == ["open_world", "truman_world"]
    assert bundles[0].root == open_world_root
    assert bundles[1].root == truman_root


def test_bundle_registry_returns_bundle_by_id(tmp_path):
    scenarios_root = tmp_path / "scenarios"
    bundle_root = scenarios_root / "truman_world"
    bundle_root.mkdir(parents=True)
    (bundle_root / "scenario.yml").write_text(
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

    registry = ScenarioBundleRegistry(scenarios_root)
    bundle = registry.get_bundle("truman_world")

    assert bundle is not None
    assert bundle.manifest.name == "Truman World"


def test_bundle_registry_prefers_bundle_agents_directory(tmp_path, monkeypatch):
    scenarios_root = tmp_path / "scenarios"
    bundle_root = scenarios_root / "truman_world"
    bundle_root.mkdir(parents=True)
    (bundle_root / "scenario.yml").write_text(
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
    agents_root = bundle_root / "agents"
    agents_root.mkdir()

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    registry = ScenarioBundleRegistry(scenarios_root)
    bundle = registry.get_bundle("truman_world")

    assert bundle is not None
    assert bundle.agents_root == agents_root


def test_resolve_agents_root_falls_back_to_project_agents_when_bundle_agents_missing(
    tmp_path, monkeypatch
):
    scenarios_root = tmp_path / "scenarios"
    bundle_root = scenarios_root / "truman_world"
    bundle_root.mkdir(parents=True)
    (bundle_root / "scenario.yml").write_text(
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
    project_agents_root = tmp_path / "agents"
    project_agents_root.mkdir()

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    resolved = resolve_agents_root_for_scenario("truman_world")

    assert resolved == project_agents_root


def test_bundle_registry_rejects_invalid_manifest(tmp_path):
    scenarios_root = tmp_path / "scenarios"
    invalid_root = scenarios_root / "broken"
    invalid_root.mkdir(parents=True)
    (invalid_root / "scenario.yml").write_text(
        "\n".join(
            [
                "name: Missing Id",
                "version: 1",
                "runtime_adapter: truman_world",
            ]
        ),
        encoding="utf-8",
    )

    registry = ScenarioBundleRegistry(scenarios_root)

    with pytest.raises(ValueError, match="Invalid scenario manifest"):
        registry.list_bundles()
