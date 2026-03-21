from __future__ import annotations

from typing import Any


def build_reactor_working_memory(
    world: dict[str, Any],
    memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    diagnostics = world.get("conversation_diagnostics")
    if not isinstance(diagnostics, dict):
        return {}

    working_memory: dict[str, Any] = {}

    current_focus = diagnostics.get("conversation_focus")
    if isinstance(current_focus, str) and current_focus:
        working_memory["current_focus"] = current_focus

    latest_update = diagnostics.get("other_party_latest_new_info")
    if isinstance(latest_update, str) and latest_update:
        working_memory["latest_other_party_update"] = latest_update

    other_party_intent = diagnostics.get("other_party_latest_intent")
    if isinstance(other_party_intent, str) and other_party_intent:
        working_memory["other_party_intent"] = other_party_intent

    conversation_phase = diagnostics.get("conversation_phase")
    if isinstance(conversation_phase, str) and conversation_phase:
        working_memory["conversation_phase"] = conversation_phase

    unresolved_item = diagnostics.get("unresolved_item")
    if isinstance(unresolved_item, str) and unresolved_item:
        working_memory["unresolved_item"] = unresolved_item

    repetition = diagnostics.get("self_recent_repetition")
    if isinstance(repetition, dict) and repetition.get("is_repeating") is True:
        repeat_type = repetition.get("type")
        repeat_span = repetition.get("repeat_span")
        if isinstance(repeat_type, str) and repeat_type:
            if isinstance(repeat_span, int) and repeat_span > 0:
                working_memory["repetition_risk"] = f"{repeat_type} x{repeat_span}"
            else:
                working_memory["repetition_risk"] = repeat_type

    if memory:
        working_memory["memory_anchor_count"] = len(memory)

    return working_memory
