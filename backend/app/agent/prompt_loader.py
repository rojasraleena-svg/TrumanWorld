from __future__ import annotations

import json
from pathlib import Path


class PromptLoader:
    """Loads prompt.md and prepares prompt text for runtime use."""

    def load(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()

    def render(self, base_prompt: str, context: dict[str, object] | None = None) -> str:
        if not context:
            return base_prompt

        lines = [base_prompt, "", "# 运行上下文", "```json", self._to_pretty_json(context), "```"]
        return "\n".join(lines)

    def render_decision_prompt(
        self,
        base_prompt: str,
        context: dict[str, object],
        allowed_actions: list[str],
    ) -> str:
        lines = [
            base_prompt,
            "",
        ]

        # 渲染对话历史（如果有）
        recent_events = context.get("recent_events", [])
        if recent_events:
            lines.append("# 最近对话")
            lines.append(
                "以下是最近发生的事件（按时间倒序）。你需要延续这些对话，而不是重复或忽略。"
            )
            lines.append("")
            for evt in reversed(recent_events):  # 按时间正序显示
                lines.append(self._format_event(evt))
            lines.append("")

        lines.extend(
            [
                "# 决策任务",
                "基于你的角色和上述对话历史，决定下一步动作。",
                f"允许的动作只有：{', '.join(allowed_actions)}。",
                "",
                "# 输出约束",
                "- 只能返回一个 JSON 对象",
                "- JSON 仅可包含字段：`action_type`、`target_location_id`、`target_agent_id`、`message`、`payload`",
                "- `action_type` 必须来自允许动作集合",
                "- 当 `action_type=move` 时，应尽量提供 `target_location_id`",
                "- 当 `action_type=move` 时，只能使用运行上下文中真实存在的地点 ID，不要编造别名、英文变体或不存在的地点",
                "- 当 `action_type=talk` 时，必须提供 `target_agent_id` 与 `message`（30-200 字的自然对话）",
                "- 如果信息不足，优先保持当前情境一致，通常返回 `rest`，不要把普通停留、等待、整理或在家活动表述成 `work`",
                "- 只有当你明确处在合理的工作场景中时，才返回 `work`；有固定工作地点的人在到达工作地点前应优先 `move` 或 `rest`",
                "- **重要**：对话要延续之前的内容，不要重复已说过的话",
                "",
                "# 运行上下文",
                "```json",
                self._to_pretty_json(context),
                "```",
            ]
        )
        return "\n".join(lines)

    def _format_event(self, evt: dict[str, object]) -> str:
        """格式化单个事件为可读文本"""
        event_type = evt.get("event_type", "unknown")
        actor_name = evt.get("actor_name", "某人")
        target_name = evt.get("target_name", "")
        tick_no = evt.get("tick_no", "?")

        if event_type == "talk":
            message = evt.get("message", "...")
            if target_name:
                return f'[Tick {tick_no}] {actor_name} → {target_name}: "{message}"'
            return f'[Tick {tick_no}] {actor_name}: "{message}"'
        elif event_type == "move":
            location = evt.get("location_name", "某地")
            return f"[Tick {tick_no}] {actor_name} 移动到了 {location}"
        elif event_type == "work":
            return f"[Tick {tick_no}] {actor_name} 正在工作"
        elif event_type == "rest":
            return f"[Tick {tick_no}] {actor_name} 正在休息"
        else:
            return f"[Tick {tick_no}] {actor_name} 执行了 {event_type}"

    def _to_pretty_json(self, payload: dict[str, object]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)
