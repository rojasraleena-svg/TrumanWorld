from __future__ import annotations

import pytest

from app.infra.settings import get_settings


def test_runtime_director_config_loads_bundle_specific_config(tmp_path, monkeypatch: pytest.MonkeyPatch):
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
    (bundle_root / "director.yml").write_text(
        "\n".join(
            [
                "enabled: true",
                "decision_interval: 11",
                "prompt:",
                "  file: director_prompt.md",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_root / "director_prompt.md").write_text(
        "Hero director prompt",
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    from app.scenario.runtime.director_config import load_director_config

    config = load_director_config("hero_world", force_reload=True)

    assert config.scenario_id == "hero_world"
    assert config.decision_interval == 11
    assert config.get_prompt_template() == "Hero director prompt"


def test_runtime_director_config_falls_back_to_default_bundle_when_specific_config_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    default_root = tmp_path / "scenarios" / "narrative_world"
    default_root.mkdir(parents=True)
    (default_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: narrative_world",
                "name: Narrative World",
                "version: 1",
                "adapter: bundle_world",
                "default: true",
            ]
        ),
        encoding="utf-8",
    )
    (default_root / "director.yml").write_text(
        "\n".join(
            [
                "enabled: true",
                "decision_interval: 7",
            ]
        ),
        encoding="utf-8",
    )

    hero_root = tmp_path / "scenarios" / "hero_world"
    hero_root.mkdir(parents=True)
    (hero_root / "scenario.yml").write_text(
        "\n".join(
            [
                "id: hero_world",
                "name: Hero World",
                "version: 1",
                "adapter: bundle_world",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TRUMANWORLD_PROJECT_ROOT", str(tmp_path))
    get_settings.cache_clear()

    from app.scenario.runtime.director_config import load_director_config

    config = load_director_config("hero_world", force_reload=True)

    assert config.scenario_id == "hero_world"
    assert config.decision_interval == 7
