from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenarioManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    adapter: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalize_adapter_alias(cls, data):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        adapter = normalized.get("adapter")
        legacy_runtime_adapter = normalized.get("runtime_adapter")
        if not isinstance(adapter, str) or not adapter:
            if isinstance(legacy_runtime_adapter, str) and legacy_runtime_adapter:
                normalized["adapter"] = legacy_runtime_adapter
        return normalized


class ScenarioSemantics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subject_role: str | None = None
    support_roles: list[str] = Field(default_factory=list)
    alert_metric: str | None = None


class ScenarioCapabilities(BaseModel):
    model_config = ConfigDict(extra="ignore")

    director: bool | None = None
    alert_tracking: bool | None = None
    scene_guidance: bool | None = None


class ScenarioBundle(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manifest: ScenarioManifest
    semantics: ScenarioSemantics = Field(default_factory=ScenarioSemantics)
    capabilities: ScenarioCapabilities = Field(default_factory=ScenarioCapabilities)
    root: Path
    manifest_path: Path

    @property
    def agents_root(self) -> Path:
        return self.root / "agents"
