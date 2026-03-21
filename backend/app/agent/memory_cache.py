"""Memory cache for in-process MCP tools.

This module provides a memory cache implementation that allows MCP tools
to query agent memories without creating database sessions, avoiding
greenlet conflicts with anyio task groups.
"""

from __future__ import annotations

from typing import Any


class MemoryCache:
    """In-memory cache for agent memories.

    This cache is pre-loaded during Phase 1 (read_session) and used
    during Phase 2 (SDK calls) to avoid creating AsyncSession in
    anyio task groups, which causes greenlet_spawn conflicts.
    """

    def __init__(self, cache_data: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """Initialize the memory cache.

        Args:
            cache_data: Pre-loaded memory data from build_agent_memory_cache.
                Structure: {
                    "short_term": [...],
                    "medium_term": [...],
                    "long_term": [...],
                    "about_others": {other_agent_id: [...]},
                    "all": [...]
                }
        """
        self._cache = cache_data or {}

    def with_working_memory(self, working_memory: dict[str, Any] | None) -> MemoryCache:
        merged_cache = dict(self._cache)
        if working_memory:
            merged_cache["working_memory"] = dict(working_memory)
        return MemoryCache(merged_cache)

    @staticmethod
    def _memory_score(memory: dict[str, Any]) -> tuple[float, float, int]:
        return (
            float(memory.get("importance") or 0.0),
            float(memory.get("self_relevance") or 0.0),
            int(memory.get("tick_no") or 0),
        )

    def search_memories(
        self,
        query: str,
        category: str = "long_term",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search memories by keyword with importance ranking.

        Args:
            query: Search keyword (case-insensitive substring match)
            category: Memory category to search ("short_term", "medium_term", "long_term", "all")
            limit: Maximum number of results

        Returns:
            List of matching memory records, sorted by importance (descending)
        """
        query_lower = query.lower()

        # Determine which memories to search
        if category == "all":
            memories = self._cache.get("all", [])
        else:
            memories = self._cache.get(category, [])

        # Collect matching memories with their importance scores
        matching = []
        for mem in memories:
            content = (mem.get("content") or "").lower()
            summary = (mem.get("summary") or "").lower()
            if query_lower in content or query_lower in summary:
                matching.append(mem)

        # Sort by importance (descending), then by tick_no (most recent first)
        matching.sort(key=lambda m: self._memory_score(m), reverse=True)

        return matching[:limit]

    def get_recent_memories(
        self,
        category: str = "all",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get most recent memories.

        Args:
            category: Memory category filter ("short_term", "medium_term", "long_term", "all")
            limit: Maximum number of results

        Returns:
            List of recent memory records (already sorted by time)
        """
        if category == "all":
            memories = self._cache.get("all", [])
        else:
            memories = self._cache.get(category, [])

        return memories[:limit]

    def get_memories_about_agent(
        self,
        other_agent_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get memories involving a specific agent.

        Args:
            other_agent_id: The other agent's ID
            limit: Maximum number of results

        Returns:
            List of memory records involving the specified agent
        """
        about_others = self._cache.get("about_others", {})
        memories = about_others.get(other_agent_id, [])
        return memories[:limit]

    def get_memories_by_location(
        self,
        location_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get memories that occurred at a specific location.

        Args:
            location_id: Location ID
            limit: Maximum number of results

        Returns:
            List of memory records at the specified location
        """
        results = []
        all_memories = self._cache.get("all", [])

        for mem in all_memories:
            if mem.get("location_id") == location_id:
                results.append(mem)
                if len(results) >= limit:
                    break

        return results

    def get_working_memory(self) -> dict[str, Any]:
        working_memory = self._cache.get("working_memory")
        if isinstance(working_memory, dict):
            return dict(working_memory)
        return {}

    def format_for_display(self, memories: list[dict[str, Any]]) -> str:
        """Format memory records for display to agent.

        Args:
            memories: List of memory records

        Returns:
            Formatted string for display
        """
        if not memories:
            return "没有找到相关记忆。"

        lines = ["找到以下记忆："]
        for i, mem in enumerate(memories, 1):
            tick_info = f"Tick {mem.get('tick_no', '?')}"
            category_info = mem.get("memory_category", "unknown")
            summary = mem.get("summary") or mem.get("content", "")[:50]
            lines.append(f"{i}. [{tick_info}] [{category_info}] {summary}")
            if mem.get("related_agent_name"):
                lines.append(f"   相关人物: {mem['related_agent_name']}")

        return "\n".join(lines)

    def format_working_memory_for_display(self, working_memory: dict[str, Any]) -> str:
        if not working_memory:
            return "当前没有可用的短时工作记忆。"

        labels = (
            ("current_focus", "当前话题"),
            ("latest_other_party_update", "对方最新进展"),
            ("other_party_intent", "对方意图"),
            ("conversation_phase", "对话阶段"),
            ("unresolved_item", "待处理项"),
            ("repetition_risk", "重复风险"),
        )
        lines = ["当前短时工作记忆："]
        for key, label in labels:
            value = working_memory.get(key)
            if isinstance(value, str) and value:
                lines.append(f"- {label}: {value}")
        return "\n".join(lines)
