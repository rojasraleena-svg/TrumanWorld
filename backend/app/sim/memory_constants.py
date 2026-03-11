"""Memory system constants and utilities.

This module defines importance scores, memory categories, and related utilities
for the memory system.
"""

from __future__ import annotations


class MemoryCategory(str):
    """Memory category for time-based classification."""

    SHORT_TERM = "short_term"  # < 30 minutes, recent events
    MEDIUM_TERM = "medium_term"  # 30 min - 6 hours, consolidated memories
    LONG_TERM = "long_term"  # > 6 hours or highly important

    @classmethod
    def all_categories(cls) -> list[str]:
        return [cls.SHORT_TERM, cls.MEDIUM_TERM, cls.LONG_TERM]


# Default importance scores by event type
# Range: 0.0 (trivial) to 1.0 (critical)
EVENT_IMPORTANCE_DEFAULTS: dict[str, float] = {
    # Social interactions - high importance
    "talk": 0.7,
    # Work activities - medium importance
    "work": 0.4,
    # Rest - low importance
    "rest": 0.2,
    # Movement - trivial
    "move": 0.1,
    # Director events - high importance
    "director_broadcast": 0.8,
    "power_outage": 0.6,
}

# Importance multipliers for special conditions
IMPORTANCE_MULTIPLIERS = {
    # Talk with emotional content
    "has_emotional_content": 1.2,
    # First interaction with someone
    "first_interaction": 1.3,
    # Event at important location
    "at_home": 1.1,
    # Long conversation (> 100 chars)
    "long_conversation": 1.15,
}


def calculate_event_importance(
    event_type: str,
    payload: dict | None = None,
    *,
    is_first_interaction: bool = False,
) -> float:
    """Calculate importance score for an event.

    Args:
        event_type: Type of the event (talk, work, move, rest, etc.)
        payload: Event payload for content analysis
        is_first_interaction: Whether this is a first interaction with someone

    Returns:
        Importance score between 0.0 and 1.0
    """
    # Get base importance for event type
    base_importance = EVENT_IMPORTANCE_DEFAULTS.get(event_type, 0.3)

    importance = base_importance
    payload = payload or {}

    # Apply multipliers
    if is_first_interaction:
        importance *= IMPORTANCE_MULTIPLIERS["first_interaction"]

    # Check for emotional content in talk events
    if event_type == "talk":
        message = payload.get("message", "")
        # Emotional indicators
        emotional_words = ["喜欢", "爱", "讨厌", "恨", "担心", "开心", "难过", "想念", "抱歉", "谢谢"]
        if any(word in message for word in emotional_words):
            importance *= IMPORTANCE_MULTIPLIERS["has_emotional_content"]

        # Long conversation bonus
        if len(message) > 100:
            importance *= IMPORTANCE_MULTIPLIERS["long_conversation"]

    # Clamp to valid range
    return min(1.0, max(0.0, importance))


def determine_memory_category(
    event_type: str,
    importance: float,
    tick_age: int = 0,
    tick_minutes: int = 5,
) -> str:
    """Determine appropriate memory category.

    Args:
        event_type: Type of the event
        importance: Importance score of the event
        tick_age: How many ticks have passed since the event
        tick_minutes: Minutes per tick

    Returns:
        Memory category (short_term, medium_term, or long_term)
    """
    # High importance events immediately become long_term candidates
    if importance >= 0.7:
        return MemoryCategory.LONG_TERM

    # Medium importance becomes medium_term
    if importance >= 0.5:
        return MemoryCategory.MEDIUM_TERM

    # Time-based classification for lower importance
    age_minutes = tick_age * tick_minutes

    if age_minutes < 30:
        return MemoryCategory.SHORT_TERM
    elif age_minutes < 360:  # 6 hours
        return MemoryCategory.MEDIUM_TERM
    else:
        return MemoryCategory.LONG_TERM


def should_consolidate_memory(
    current_category: str,
    importance: float,
    access_count: int,
    tick_age: int,
    tick_minutes: int = 5,
) -> bool:
    """Determine if a memory should be consolidated to a higher category.

    Args:
        current_category: Current memory category
        importance: Importance score
        access_count: Number of times this memory was accessed
        tick_age: How many ticks since creation
        tick_minutes: Minutes per tick

    Returns:
        True if memory should be consolidated
    """
    if current_category == MemoryCategory.LONG_TERM:
        return False  # Already at highest

    # High access count promotes consolidation
    if access_count >= 3:
        return True

    # High importance memories consolidate faster
    age_minutes = tick_age * tick_minutes
    if importance >= 0.6 and age_minutes >= 60:
        return True

    # Time-based consolidation
    if current_category == MemoryCategory.SHORT_TERM:
        if age_minutes >= 120:  # 2 hours
            return True

    return False
