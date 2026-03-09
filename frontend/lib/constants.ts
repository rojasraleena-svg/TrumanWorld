// 事件筛选器常量
export const EVENT_FILTERS = [
  { id: "all", label: "全部事件" },
  { id: "social", label: "对话" },
  { id: "activity", label: "动作" },
  { id: "movement", label: "移动" },
] as const;

export type EventFilterId = (typeof EVENT_FILTERS)[number]["id"];
