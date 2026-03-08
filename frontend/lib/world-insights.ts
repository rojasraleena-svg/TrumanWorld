import type { WorldEvent, WorldSnapshot, AgentSummary } from "@/lib/types";
import {
  EVENT_MOVE,
  EVENT_TALK,
  EVENT_WORK,
  EVENT_REST,
} from "@/lib/simulation-protocol";

// ============================================================================
// 类型定义
// ============================================================================

export type Trend = "up" | "down" | "stable";

export interface WorldHealthMetrics {
  continuityScore: number;
  continuityTrend: Trend;
  continuityIssue?: string;

  socialActivity: number;
  socialTrend: Trend;

  trumanSuspicion: number;
  suspicionTrend: Trend;

  directorStats: {
    total: number;
    executed: number;
    executionRate: number;
  };

  activitySummary: {
    working: number;
    resting: number;
    commuting: number;
    total: number;
  };

  recentTalkCount: number;
  recentMoveCount: number;
  recentRejectionCount: number;
}

export interface StoryEvent {
  id: string;
  tickNo: number;
  time: string;
  type: "talk" | "move" | "work" | "rest" | "rejection" | "other";
  actorName: string;
  targetName?: string;
  locationName?: string;
  description: string;
  icon: string;
}

export interface StoryChapter {
  id: string;
  timeLabel: string;
  period: "dawn" | "morning" | "noon" | "afternoon" | "evening" | "night";
  periodIcon: string;
  periodName: string;
  events: StoryEvent[];
  highlights: {
    type: "normal" | "warning" | "social" | "work";
    description: string;
  }[];
}

// ============================================================================
// 世界健康度计算
// ============================================================================

export function calculateWorldHealthMetrics(
  world: WorldSnapshot,
  directorMemories?: Array<{ was_executed: boolean }>,
): WorldHealthMetrics {
  const events = world.recent_events;
  const agents = world.locations.flatMap((l) => l.occupants);

  // 1. 剧情连贯性：基于拒绝事件计算
  const rejectionEvents = events.filter(
    (e) => e.event_type === "move_rejected" || e.event_type === "talk_rejected",
  );
  const continuityScore = Math.max(0, 100 - rejectionEvents.length * 15);
  const continuityTrend: Trend =
    rejectionEvents.length > 0 ? "down" : "stable";
  const continuityIssue =
    rejectionEvents.length > 0
      ? getRejectionDescription(rejectionEvents[0], agents)
      : undefined;

  // 2. 社交活跃度：基于对话事件频率 (假设50个tick内有10次对话为100%)
  const talkEvents = events.filter((e) => e.event_type === EVENT_TALK);
  const socialActivity = Math.min(100, (talkEvents.length / 10) * 100);
  const socialTrend: Trend =
    talkEvents.length > 5 ? "up" : talkEvents.length > 0 ? "stable" : "down";

  // 3. Truman怀疑度
  const truman = agents.find((a) => a.name === "Truman");
  const trumanSuspicion =
    ((truman?.status?.suspicion_score as number) ?? 0) * 100;
  const suspicionTrend: Trend = "stable";

  // 4. 导演干预统计（如果后端提供数据）
  const totalMemories = directorMemories?.length ?? 0;
  const executedMemories =
    directorMemories?.filter((m) => m.was_executed).length ?? 0;
  
  // 5. 活动摘要
  const activitySummary = calculateActivitySummary(agents, world.locations);

  return {
    continuityScore: Math.round(continuityScore),
    continuityTrend,
    continuityIssue,

    socialActivity: Math.round(socialActivity),
    socialTrend,

    trumanSuspicion: Math.round(trumanSuspicion),
    suspicionTrend,

    directorStats: {
      total: totalMemories,
      executed: executedMemories,
      executionRate:
        totalMemories > 0
          ? Math.round((executedMemories / totalMemories) * 100)
          : 0,
    },

    activitySummary,

    recentTalkCount: talkEvents.length,
    recentMoveCount: events.filter((e) => e.event_type === EVENT_MOVE).length,
    recentRejectionCount: rejectionEvents.length,
  };
}

function getRejectionDescription(
  event: WorldEvent,
  agents: AgentSummary[],
): string {
  const actor = agents.find((a) => a.id === event.actor_agent_id);
  const reason = (event.payload?.reason as string) ?? "未知原因";
  const actorName = actor?.name ?? "某人";

  if (reason === "location_not_found") {
    return `${actorName}移动受阻：地点不存在`;
  }
  return `${actorName}动作被拒绝`;
}

function calculateActivitySummary(agents: AgentSummary[], locations: WorldSnapshot["locations"]) {
  let working = 0;
  let resting = 0;
  let commuting = 0;
  const locationTypeMap = new Map(locations.map((location) => [location.id, location.location_type]));

  for (const agent of agents) {
    const goal = agent.current_goal?.toLowerCase() ?? "";
    const locationType = agent.current_location_id
      ? locationTypeMap.get(agent.current_location_id)
      : undefined;
    const isWorkContext = locationType != null && locationType !== "home" && locationType !== "plaza";

    if (goal === "work") {
      if (isWorkContext) {
        working++;
      } else {
        commuting++;
      }
    } else if (goal === "rest" || goal === "wander") {
      resting++;
    } else if (goal === "commute") {
      commuting++;
    } else {
      resting++;
    }
  }

  return {
    working,
    resting,
    commuting,
    total: agents.length,
  };
}

// ============================================================================
// 故事时间线聚合
// ============================================================================

const PERIOD_CONFIG = {
  dawn: { icon: "🌅", name: "黎明" },
  morning: { icon: "🌄", name: "早晨" },
  noon: { icon: "☀️", name: "正午" },
  afternoon: { icon: "🌤️", name: "下午" },
  evening: { icon: "🌇", name: "傍晚" },
  night: { icon: "🌙", name: "夜晚" },
};

export function aggregateStoryChapters(
  world: WorldSnapshot,
): StoryChapter[] {
  const events = world.recent_events;
  const { agentNameMap, locationNameMap } = buildNameMaps(world);

  // 按时间段分组事件
  const groupedEvents = groupEventsByTimePeriod(events, world);
  const chapters: StoryChapter[] = [];

  for (const [period, periodEvents] of Object.entries(groupedEvents)) {
    if (periodEvents.length === 0) continue;

    const config = PERIOD_CONFIG[period as keyof typeof PERIOD_CONFIG];
    const storyEvents = periodEvents
      .map((e) => convertToStoryEvent(e, agentNameMap, locationNameMap))
      .filter(Boolean) as StoryEvent[];

    if (storyEvents.length === 0) continue;

    // 生成时间标签
    const timeRange = getTimeRange(periodEvents, world);

    // 提取亮点
    const highlights = extractHighlights(storyEvents);

    chapters.push({
      id: `${period}-${world.run.current_tick}`,
      timeLabel: timeRange,
      period: period as StoryChapter["period"],
      periodIcon: config.icon,
      periodName: config.name,
      events: storyEvents.slice(0, 5), // 最多显示5个事件
      highlights,
    });
  }

  // 按时间倒序排列（最新的在前面）
  return chapters.reverse();
}

function buildNameMaps(world: WorldSnapshot) {
  const agentNameMap: Record<string, string> = {};
  const locationNameMap: Record<string, string> = {};

  for (const location of world.locations) {
    locationNameMap[location.id] = location.name;
    for (const agent of location.occupants) {
      agentNameMap[agent.id] = agent.name;
    }
  }

  return { agentNameMap, locationNameMap };
}

function groupEventsByTimePeriod(
  events: WorldEvent[],
  world: WorldSnapshot,
): Record<string, WorldEvent[]> {
  const groups: Record<string, WorldEvent[]> = {
    dawn: [],
    morning: [],
    noon: [],
    afternoon: [],
    evening: [],
    night: [],
  };

  const tickMinutes = world.run.tick_minutes ?? 5;
  const baseTick = world.run.current_tick ?? 0;

  for (const event of events) {
    const hour = getEventHour(event.tick_no, baseTick, tickMinutes, world);
    const period = getPeriodFromHour(hour);
    groups[period].push(event);
  }

  return groups;
}

function getEventHour(
  tickNo: number,
  baseTick: number,
  tickMinutes: number,
  world: WorldSnapshot,
): number {
  if (world.world_clock) {
    const offsetMinutes = (tickNo - baseTick) * tickMinutes;
    const baseHour = world.world_clock.hour;
    const baseMinute = world.world_clock.minute;
    const totalMinutes = baseHour * 60 + baseMinute + offsetMinutes;
    return Math.floor(((totalMinutes % 1440) + 1440) % 1440) / 60;
  }
  // 默认：tick 0 是早上7点
  const totalMinutes = tickNo * tickMinutes + 7 * 60;
  return Math.floor((totalMinutes % 1440) / 60);
}

function getPeriodFromHour(hour: number): string {
  if (hour >= 5 && hour < 7) return "dawn";
  if (hour >= 7 && hour < 12) return "morning";
  if (hour >= 12 && hour < 14) return "noon";
  if (hour >= 14 && hour < 18) return "afternoon";
  if (hour >= 18 && hour < 21) return "evening";
  return "night";
}

function convertToStoryEvent(
  event: WorldEvent,
  agentNameMap: Record<string, string>,
  locationNameMap: Record<string, string>,
): StoryEvent | null {
  const actorName =
    event.actor_name ?? agentNameMap[event.actor_agent_id ?? ""] ?? "某人";
  const targetName =
    event.target_name ?? agentNameMap[event.target_agent_id ?? ""];
  const locationName =
    event.location_name ?? locationNameMap[event.location_id ?? ""];

  let type: StoryEvent["type"] = "other";
  let description = "";
  let icon = "";

  switch (event.event_type) {
    case EVENT_TALK:
      type = "talk";
      icon = "💬";
      if (targetName) {
        description = `${actorName} 与 ${targetName} 交谈`;
      } else {
        description = `${actorName} 在说话`;
      }
      break;

    case EVENT_MOVE:
      type = "move";
      icon = "🚶";
      const toLocation =
        (event.payload?.to_location_name as string) ?? locationName ?? "某处";
      description = `${actorName} 前往 ${toLocation}`;
      break;

    case EVENT_WORK:
      type = "work";
      icon = "⚒️";
      description = `${actorName} 正在工作`;
      break;

    case EVENT_REST:
      type = "rest";
      icon = "😴";
      description = `${actorName} 正在休息`;
      break;

    case "move_rejected":
    case "talk_rejected":
      type = "rejection";
      icon = "⚠️";
      description = `${actorName} 的动作被拒绝`;
      break;

    default:
      return null;
  }

  return {
    id: event.id,
    tickNo: event.tick_no,
    time: `T${event.tick_no}`,
    type,
    actorName,
    targetName,
    locationName,
    description,
    icon,
  };
}

function getTimeRange(
  events: WorldEvent[],
  world: WorldSnapshot,
): string {
  if (events.length === 0) return "";

  const tickMinutes = world.run.tick_minutes ?? 5;
  const baseTick = world.run.current_tick ?? 0;

  const minTick = Math.min(...events.map((e) => e.tick_no));
  const maxTick = Math.max(...events.map((e) => e.tick_no));

  const startHour = getEventHour(minTick, baseTick, tickMinutes, world);
  const endHour = getEventHour(maxTick, baseTick, tickMinutes, world);

  const startStr = `${Math.floor(startHour)}:00`;
  const endStr = `${Math.floor(endHour)}:00`;

  if (startStr === endStr) return startStr;
  return `${startStr} - ${endStr}`;
}

function extractHighlights(
  events: StoryEvent[],
): StoryChapter["highlights"] {
  const highlights: StoryChapter["highlights"] = [];

  // 统计各类事件
  const talkCount = events.filter((e) => e.type === "talk").length;
  const rejectionCount = events.filter((e) => e.type === "rejection").length;
  const moveCount = events.filter((e) => e.type === "move").length;

  if (rejectionCount > 0) {
    highlights.push({
      type: "warning",
      description: `${rejectionCount} 个异常`,
    });
  }

  if (talkCount > 0) {
    highlights.push({
      type: "social",
      description: `${talkCount} 次对话`,
    });
  }

  if (moveCount > 0) {
    highlights.push({
      type: "normal",
      description: `${moveCount} 次移动`,
    });
  }

  if (highlights.length === 0) {
    highlights.push({
      type: "normal",
      description: "小镇平静运转",
    });
  }

  return highlights;
}

// ============================================================================
// 格式化工具
// ============================================================================

export function formatMetricValue(value: number, unit?: string): string {
  if (unit) {
    return `${value}${unit}`;
  }
  return `${value}`;
}

export function getTrendIcon(trend: Trend): string {
  switch (trend) {
    case "up":
      return "↑";
    case "down":
      return "↓";
    case "stable":
      return "→";
  }
}

export function getTrendColor(trend: Trend): string {
  switch (trend) {
    case "up":
      return "text-emerald-600";
    case "down":
      return "text-amber-600";
    case "stable":
      return "text-slate-500";
  }
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

export function getScoreBgColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}
