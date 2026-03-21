"use client";

import { useMemo, useState } from "react";

import {
  formatAgentScore,
  formatMemoryCategory,
  memoryCategoryBadgeClass,
} from "@/lib/agent-utils";
import { describeAgentEvent } from "@/lib/event-utils";
import { tickToSimDayTime } from "@/lib/world-utils";
import type { AgentDetailFilter, AgentDetails, AgentMemory, AgentRecentEvent, WorldSnapshot } from "@/lib/types";

type AgentSignalsPanelProps = {
  agent: AgentDetails;
  world?: WorldSnapshot | null;
  initialFilter?: AgentDetailFilter;
  compact?: boolean;
};

type LocalFilterState = {
  eventType: string;
  eventQuery: string;
  hideRoutineEvents: boolean;
  memoryCategory: string;
  memoryQuery: string;
  minMemoryImportance: string;
};

const ROUTINE_EVENT_TYPES = new Set(["work", "rest"]);

function applyEventFilters(events: AgentRecentEvent[], filter: LocalFilterState) {
  const query = filter.eventQuery.trim().toLowerCase();
  return events.filter((event) => {
    if (filter.eventType && event.event_type !== filter.eventType) return false;
    if (filter.hideRoutineEvents && ROUTINE_EVENT_TYPES.has(event.event_type)) return false;
    if (!query) return true;
    const haystacks = [
      event.event_type,
      event.actor_name,
      event.target_name,
      event.location_name,
      typeof event.payload.message === "string" ? event.payload.message : undefined,
      describeAgentEvent(event),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystacks.includes(query);
  });
}

function applyMemoryFilters(memories: AgentMemory[], filter: LocalFilterState) {
  const query = filter.memoryQuery.trim().toLowerCase();
  const minImportance = filter.minMemoryImportance ? Number(filter.minMemoryImportance) : null;
  return memories.filter((memory) => {
    if (filter.memoryCategory && memory.memory_category !== filter.memoryCategory) return false;
    if (minImportance != null && (memory.importance ?? 0) < minImportance) return false;
    if (!query) return true;
    const haystacks = [
      memory.summary,
      memory.content,
      memory.related_agent_name,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystacks.includes(query);
  });
}

export function AgentSignalsPanel({
  agent,
  world,
  initialFilter,
  compact = false,
}: AgentSignalsPanelProps) {
  const [filter, setFilter] = useState<LocalFilterState>({
    eventType: initialFilter?.event_type ?? "",
    eventQuery: initialFilter?.event_query ?? "",
    hideRoutineEvents: initialFilter?.include_routine_events === false,
    memoryCategory: initialFilter?.memory_category ?? "",
    memoryQuery: initialFilter?.memory_query ?? "",
    minMemoryImportance:
      initialFilter?.min_memory_importance != null
        ? String(initialFilter.min_memory_importance)
        : "",
  });

  const eventTypeOptions = useMemo(
    () => Array.from(new Set(agent.recent_events.map((event) => event.event_type))),
    [agent.recent_events],
  );
  const filteredEvents = useMemo(
    () => applyEventFilters(agent.recent_events, filter),
    [agent.recent_events, filter],
  );
  const filteredMemories = useMemo(
    () => applyMemoryFilters(agent.memories, filter),
    [agent.memories, filter],
  );

  return (
    <div className={`grid gap-6 ${compact ? "" : "xl:grid-cols-2"}`}>
      <section className="flex min-h-0 flex-col rounded-[28px] border border-white/70 bg-white/80 p-5 shadow-xs backdrop-blur-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">近期事件</p>
            <h2 className="mt-1 text-lg font-semibold text-ink">角色行为流</h2>
          </div>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-500">
            {filteredEvents.length} / {agent.recent_events.length}
          </span>
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <FilterField label="事件类型" htmlFor="agent-event-type">
            <select
              id="agent-event-type"
              value={filter.eventType}
              onChange={(event) => setFilter((current) => ({ ...current, eventType: event.target.value }))}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">全部事件</option>
              {eventTypeOptions.map((eventType) => (
                <option key={eventType} value={eventType}>
                  {eventType}
                </option>
              ))}
            </select>
          </FilterField>
          <FilterField label="事件搜索" htmlFor="agent-event-query">
            <input
              id="agent-event-query"
              value={filter.eventQuery}
              onChange={(event) => setFilter((current) => ({ ...current, eventQuery: event.target.value }))}
              placeholder="消息、地点、对象"
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            />
          </FilterField>
          <label
            htmlFor="agent-hide-routine"
            className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-3 py-2 text-sm text-slate-600"
          >
            <input
              id="agent-hide-routine"
              type="checkbox"
              checked={filter.hideRoutineEvents}
              onChange={(event) =>
                setFilter((current) => ({ ...current, hideRoutineEvents: event.target.checked }))
              }
            />
            <span>隐藏例行事件</span>
          </label>
        </div>

        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
          {filteredEvents.length === 0 ? (
            <p className="rounded-2xl bg-slate-50 px-4 py-4 text-sm text-slate-500">暂无匹配事件。</p>
          ) : (
            filteredEvents.map((event) => {
              const isRoutine = ROUTINE_EVENT_TYPES.has(event.event_type);
              const timeLabel = world
                ? tickToSimDayTime(
                    event.tick_no,
                    world.run.tick_minutes ?? 5,
                    world.run.current_tick ?? 0,
                    world.world_clock?.iso,
                  )
                : null;
              return (
                <article
                  key={event.id}
                  className={`rounded-2xl px-3 py-2.5 ${
                    isRoutine ? "bg-slate-50/70 text-slate-500" : "border border-slate-100 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-[10px] uppercase tracking-wider text-slate-400">{event.event_type}</p>
                      <p className="truncate text-sm">{describeAgentEvent(event)}</p>
                    </div>
                    <span className="shrink-0 text-[11px] text-slate-400">
                      T{event.tick_no}
                      {timeLabel ? ` · ${timeLabel}` : ""}
                    </span>
                  </div>
                  {(event.target_name || event.location_name) && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {event.target_name ? (
                        <span className="rounded-full border border-rose-100 bg-rose-50 px-2 py-0.5 text-[10px] text-rose-600">
                          → {event.target_name}
                        </span>
                      ) : null}
                      {event.location_name ? (
                        <span className="rounded-full border border-slate-100 bg-slate-50 px-2 py-0.5 text-[10px] text-slate-500">
                          📍 {event.location_name}
                        </span>
                      ) : null}
                    </div>
                  )}
                </article>
              );
            })
          )}
        </div>
      </section>

      <section className="flex min-h-0 flex-col rounded-[28px] border border-white/70 bg-white/80 p-5 shadow-xs backdrop-blur-sm">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">记忆</p>
            <h2 className="mt-1 text-lg font-semibold text-ink">内部记忆栈</h2>
          </div>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-500">
            {filteredMemories.length} / {agent.memories.length}
          </span>
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <FilterField label="记忆层级" htmlFor="agent-memory-category">
            <select
              id="agent-memory-category"
              value={filter.memoryCategory}
              onChange={(event) =>
                setFilter((current) => ({ ...current, memoryCategory: event.target.value }))
              }
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">全部层级</option>
              <option value="short_term">短期</option>
              <option value="medium_term">中期</option>
              <option value="long_term">长期</option>
            </select>
          </FilterField>
          <FilterField label="记忆搜索" htmlFor="agent-memory-query">
            <input
              id="agent-memory-query"
              value={filter.memoryQuery}
              onChange={(event) => setFilter((current) => ({ ...current, memoryQuery: event.target.value }))}
              placeholder="摘要、内容、关联对象"
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            />
          </FilterField>
          <FilterField label="最低重要性" htmlFor="agent-memory-importance">
            <select
              id="agent-memory-importance"
              value={filter.minMemoryImportance}
              onChange={(event) =>
                setFilter((current) => ({ ...current, minMemoryImportance: event.target.value }))
              }
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">全部重要性</option>
              <option value="0.3">0.3+</option>
              <option value="0.5">0.5+</option>
              <option value="0.8">0.8+</option>
              <option value="0.95">0.95+</option>
            </select>
          </FilterField>
        </div>

        <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {filteredMemories.length === 0 ? (
            <p className="rounded-2xl bg-slate-50 px-4 py-4 text-sm text-slate-500">暂无匹配记忆。</p>
          ) : (
            filteredMemories.map((memory) => (
              <article
                key={memory.id}
                className={`rounded-2xl px-3 py-2.5 ${
                  (memory.importance ?? 0) < 0.3
                    ? "bg-slate-50/70"
                    : "border border-violet-100 bg-violet-50/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm leading-5 text-ink">{memory.content}</p>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <span className="rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-[10px] text-violet-600">
                      ★ {formatAgentScore(memory.importance)}
                    </span>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] ${memoryCategoryBadgeClass(memory.memory_category)}`}
                    >
                      {formatMemoryCategory(memory.memory_category)}
                    </span>
                    {memory.related_agent_name ? (
                      <span className="rounded-full border border-rose-100 bg-rose-50 px-2 py-0.5 text-[10px] text-rose-600">
                        {memory.related_agent_name}
                      </span>
                    ) : null}
                  </div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function FilterField({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-xs font-medium text-slate-500">
        {label}
      </label>
      {children}
    </div>
  );
}
