from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class AgentCapabilities(BaseModel):
    reflection: bool = True
    dialogue: bool = True
    mcp: bool = False
    subagents: bool = False


class WorkSchedule(BaseModel):
    """工作日程配置"""

    start_hour: int | None = None
    end_hour: int | None = None
    work_days: list[str] | None = None
    type: str | None = None  # 如 "shift" 表示轮班
    shifts: list[str] | None = None


class AgentModelConfig(BaseModel):
    max_turns: int = 8
    max_budget_usd: float = 1.0


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    world_role: Literal["truman", "cast", "npc"] = "cast"
    occupation: str = "resident"
    workplace: str | None = None
    work_schedule: WorkSchedule | None = None
    home: str
    personality: dict = Field(default_factory=dict)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    model: AgentModelConfig = Field(default_factory=AgentModelConfig)
    root_dir: Path | None = None

    @property
    def prompt_path(self) -> Path:
        if self.root_dir is None:
            msg = "Agent root_dir is not set"
            raise ValueError(msg)
        return self.root_dir / "prompt.md"

    @property
    def logo_path(self) -> Path | None:
        """Return the path to the agent's logo SVG file, if it exists."""
        if self.root_dir is None:
            return None
        logo = self.root_dir / "logo.svg"
        return logo if logo.exists() else None

    @property
    def logo_url(self) -> str | None:
        """Return the URL path to the agent's logo for frontend use."""
        # Logo files are served from /agents/{agent_id}.svg
        return f"/agents/{self.id}.svg"


class AgentConfigLoader:
    """Parses agent.yml files into runtime configuration."""

    def load(self, path: Path) -> AgentConfig:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}

        config = AgentConfig.model_validate(raw)
        config.root_dir = path.parent
        return config
