from __future__ import annotations

from pathlib import Path


class PromptLoader:
    """Loads prompt.md and prepares prompt text for runtime use."""

    def load(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()

    def render(self, base_prompt: str, context: dict[str, object] | None = None) -> str:
        if not context:
            return base_prompt

        lines = [base_prompt, "", "# 运行上下文"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
