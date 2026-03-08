from pathlib import Path

from app.agent.config_loader import (
    AgentConfig,
    AgentConfigLoader,
    AgentInitialConfig,
    InitialConfigLoader,
    RelationConfig,
    RelationsLoader,
)
from app.agent.prompt_loader import PromptLoader


class AgentRegistry:
    """Loads agent configurations from the agents directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._config_loader = AgentConfigLoader()
        self._prompt_loader = PromptLoader()
        self._relations_loader = RelationsLoader()
        self._initial_loader = InitialConfigLoader()

    def list_agent_dirs(self) -> list[Path]:
        if not self.root.exists():
            return []

        return sorted(
            path
            for path in self.root.iterdir()
            if path.is_dir() and not path.name.startswith("_") and (path / "agent.yml").exists()
        )

    def list_configs(self) -> list[AgentConfig]:
        return [self._config_loader.load(path / "agent.yml") for path in self.list_agent_dirs()]

    def get_config(self, agent_id: str) -> AgentConfig | None:
        for config in self.list_configs():
            if config.id == agent_id:
                return config
        return None

    def get_agent_dir(self, agent_id: str) -> Path | None:
        """Get the directory path for an agent."""
        config = self.get_config(agent_id)
        if config is None or config.root_dir is None:
            return None
        return config.root_dir

    def get_prompt(self, agent_id: str, context: dict[str, object] | None = None) -> str | None:
        config = self.get_config(agent_id)
        if config is None:
            return None

        prompt = self._prompt_loader.load(config.prompt_path)
        return self._prompt_loader.render(prompt, context=context)

    def get_relations(self, agent_id: str) -> dict[str, RelationConfig]:
        """Load relations.yml for an agent.

        Returns a dict mapping other_agent_id -> RelationConfig.
        Returns empty dict if no relations.yml exists.
        """
        agent_dir = self.get_agent_dir(agent_id)
        if agent_dir is None:
            return {}
        return self._relations_loader.load(agent_dir / "relations.yml")

    def get_initial(self, agent_id: str) -> AgentInitialConfig:
        """Load initial.yml for an agent.

        Returns default AgentInitialConfig if no initial.yml exists.
        """
        agent_dir = self.get_agent_dir(agent_id)
        if agent_dir is None:
            return AgentInitialConfig()
        return self._initial_loader.load(agent_dir / "initial.yml")

    def get_bio(self, agent_id: str) -> str | None:
        """Load bio.md for an agent.

        Returns None if no bio.md exists.
        """
        agent_dir = self.get_agent_dir(agent_id)
        if agent_dir is None:
            return None
        bio_path = agent_dir / "bio.md"
        if not bio_path.exists():
            return None
        return bio_path.read_text(encoding="utf-8").strip()

    def load_all_relations(self) -> dict[tuple[str, str], RelationConfig]:
        """Load all relations from all agents.

        Returns a dict mapping (from_agent_id, to_agent_id) -> RelationConfig.
        This is useful for seed.py to create all relationships at once.
        """
        all_relations: dict[tuple[str, str], RelationConfig] = {}
        for config in self.list_configs():
            relations = self.get_relations(config.id)
            for other_id, rel_config in relations.items():
                all_relations[(config.id, other_id)] = rel_config
        return all_relations
