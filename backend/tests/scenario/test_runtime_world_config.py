from __future__ import annotations

import pytest

from app.infra.settings import get_settings


def test_runtime_world_config_loads_bundle_specific_world_yaml(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    bundle_root = tmp_path / "scenarios" / "hero_world"
    bundle_root.mkdir(parents=True)
    (bundle_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_root / "world.yml").write_text(
        "\n".join(
            [
                "daily_rhythm:",
                "  lunch_time: 12:00-13:00",
                "location_purposes:",
                "  plaza:",
                "    - gather",
                "social_norms:",
                "  - stay calm",
                "location_descriptions:",
                "  plaza: central square",
                "time_suggestions:",
                "  noon: eat together",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    from app.scenario.runtime.world_config import load_world_config

    config = load_world_config("hero_world", force_reload=True)

    assert config["daily_rhythm"]["lunch_time"] == "12:00-13:00"
    assert config["location_purposes"]["plaza"] == ["gather"]


def test_runtime_world_config_falls_back_to_default_bundle_when_specific_world_yaml_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    default_root = tmp_path / "scenarios" / "hero_world"
    default_root.mkdir(parents=True)
    (default_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (default_root / "world.yml").write_text(
        "\n".join(
            [
                "daily_rhythm:",
                "  lunch_time: 13:00-14:00",
                "social_norms:",
                "  - follow the festival clock",
            ]
        ),
        encoding="utf-8",
    )

    other_root = tmp_path / "scenarios" / "mystery_world"
    other_root.mkdir(parents=True)
    (other_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: mystery_world",
                "name: Mystery World",
                "version: 1",
                "adapter: bundle_world",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    from app.scenario.runtime.world_config import load_world_config

    config = load_world_config("mystery_world", force_reload=True)

    assert config["daily_rhythm"]["lunch_time"] == "13:00-14:00"
    assert config["social_norms"] == ["follow the festival clock"]


def test_runtime_world_config_builds_common_knowledge_from_world_yaml(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    bundle_root = tmp_path / "scenarios" / "hero_world"
    bundle_root.mkdir(parents=True)
    (bundle_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_root / "world.yml").write_text(
        "\n".join(
            [
                "daily_rhythm:",
                "  lunch_time: 12:00-13:00",
                "location_purposes:",
                "  plaza:",
                "    - gather",
                "social_norms:",
                "  - stay calm",
                "location_descriptions:",
                "  plaza: central square",
                "time_suggestions:",
                "  noon: eat together",
                "locations:",
                "  - id_suffix: plaza",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    from app.scenario.runtime.world_config import build_world_common_knowledge

    knowledge = build_world_common_knowledge("hero_world")

    assert knowledge == {
        "daily_rhythm": {"lunch_time": "12:00-13:00"},
        "location_purposes": {"plaza": ["gather"]},
        "social_norms": ["stay calm"],
        "location_descriptions": {"plaza": "central square"},
        "time_suggestions": {"noon": "eat together"},
    }


def test_runtime_world_config_cache_is_isolated_by_project_root(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    root_a = tmp_path / "proj_a"
    bundle_a = root_a / "scenarios" / "hero_world"
    bundle_a.mkdir(parents=True)
    (bundle_a / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_a / "world.yml").write_text("social_norms:\n  - root a\n", encoding="utf-8")

    root_b = tmp_path / "proj_b"
    bundle_b = root_b / "scenarios" / "hero_world"
    bundle_b.mkdir(parents=True)
    (bundle_b / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_b / "world.yml").write_text("social_norms:\n  - root b\n", encoding="utf-8")

    from app.scenario.runtime.world_config import load_world_config

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(root_a))
    get_settings.cache_clear()
    config_a = load_world_config("hero_world", force_reload=True)

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(root_b))
    get_settings.cache_clear()
    config_b = load_world_config("hero_world")

    assert config_a["social_norms"] == ["root a"]
    assert config_b["social_norms"] == ["root b"]
