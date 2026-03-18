from __future__ import annotations

from pathlib import Path

import yaml

from app.infra.settings import get_settings
from app.scenario.bundle_models import ScenarioBundle, ScenarioManifest


class ScenarioBundleRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root

    def list_bundles(self) -> list[ScenarioBundle]:
        if not self.root.exists():
            return []

        bundles: list[ScenarioBundle] = []
        for bundle_root in sorted(path for path in self.root.iterdir() if path.is_dir()):
            manifest_path = bundle_root / "scenario.yml"
            if not manifest_path.exists():
                continue
            bundles.append(self._load_bundle(manifest_path))
        return bundles

    def get_bundle(self, scenario_id: str | None) -> ScenarioBundle | None:
        if not scenario_id:
            return None
        for bundle in self.list_bundles():
            if bundle.manifest.id == scenario_id:
                return bundle
        return None

    def _load_bundle(self, manifest_path: Path) -> ScenarioBundle:
        with manifest_path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}

        try:
            manifest = ScenarioManifest.model_validate(raw)
        except Exception as exc:
            msg = f"Invalid scenario manifest: {manifest_path}"
            raise ValueError(msg) from exc

        return ScenarioBundle(
            manifest=manifest,
            root=manifest_path.parent,
            manifest_path=manifest_path,
        )


def get_scenario_bundle_registry() -> ScenarioBundleRegistry:
    settings = get_settings()
    return ScenarioBundleRegistry(settings.project_root / "scenarios")
