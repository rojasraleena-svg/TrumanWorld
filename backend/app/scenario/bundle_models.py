from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ScenarioManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    runtime_adapter: str = Field(min_length=1)


class ScenarioBundle(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manifest: ScenarioManifest
    root: Path
    manifest_path: Path

    @property
    def agents_root(self) -> Path:
        return self.root / "agents"
