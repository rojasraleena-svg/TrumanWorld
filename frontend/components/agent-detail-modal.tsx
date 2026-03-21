"use client";

import { useEffect, useState } from "react";
import { Modal } from "@/components/modal";
import { AgentAvatar } from "@/components/agent-avatar";
import { AgentSignalsPanel } from "@/components/agent-signals-panel";
import {
  inferAgentStatus,
  relationshipTone,
} from "@/lib/agent-utils";
import { getAgentResult } from "@/lib/api";
import { useWorld } from "@/components/world-context";
import type { AgentDetails, AgentRelationship } from "@/lib/types";

// 人格特质中文映射
const PERSONALITY_LABELS: Record<string, string> = {
  openness: "开放性",
  conscientiousness: "尽责性",
  extraversion: "外向性",
  agreeableness: "宜人性",
  neuroticism: "神经质",
  charisma: "魅力",
  humor: "幽默",
  empathy: "同理心",
  confidence: "自信",
  optimism: "乐观",
};

// 角色配置中文映射
const PROFILE_LABELS: Record<string, string> = {
  bio: "个人简介",
  world_role: "世界角色",
  workplace: "工作地点",
  work_description: "工作描述",
  home: "居住地",
  occupation: "职业",
  capabilities: "能力",
  model: "模型配置",
  work_schedule: "工作时间",
};

interface AgentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  runId: string;
  agentId: string;
}

export function AgentDetailModal({ isOpen, onClose, runId, agentId }: AgentDetailModalProps) {
  const { world } = useWorld();
  const [agent, setAgent] = useState<AgentDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllRelationships, setShowAllRelationships] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    getAgentResult(runId, agentId)
      .then((agentRes) => {
        if (agentRes.data) {
          setAgent(agentRes.data);
          return;
        }
        setError(agentRes.error === "network_error" ? "网络错误" : "未找到智能体");
      })
      .catch(() => setError("加载失败"))
      .finally(() => setLoading(false));
  }, [isOpen, runId, agentId]);

  if (loading) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        variant="inspector"
        showCloseButton={false}
        title="智能体详情"
      >
        <div className="flex h-64 items-center justify-center text-slate-400">
          <div className="mr-2 h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-moss" />
          加载中...
        </div>
      </Modal>
    );
  }

  if (error || !agent) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        variant="panel"
        showCloseButton={false}
        title="智能体详情"
      >
        <div className="flex h-64 items-center justify-center text-amber-600">
          ⚠️ {error || "未找到智能体"}
        </div>
      </Modal>
    );
  }

  const status = inferAgentStatus(agent.agent_id, agent.recent_events);
  const personality = agent.personality || {};
  const profile = agent.profile || {};
  const relationships = agent.relationships || [];
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      variant="inspector"
      showCloseButton={false}
      title="智能体详情"
    >
      <div className="flex min-h-0 flex-1 overflow-hidden">
        {/* 左侧：基本信息 */}
        <aside className="flex w-80 shrink-0 flex-col border-r border-slate-100 bg-slate-50/50">
          <div className="flex-1 overflow-y-auto p-4">
            {/* 头像和状态 */}
            <section className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-xs backdrop-blur-sm">
              <div className="flex items-center gap-4">
                <AgentAvatar
                  agentId={agent.agent_id}
                  name={agent.name}
                  occupation={agent.occupation}
                  status={status}
                  size="lg"
                  configId={agent.config_id}
                />
                <div>
                  <p className="text-lg font-semibold text-ink">{agent.name}</p>
                  <p className="text-sm text-slate-500">{agent.occupation || "居民"}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    当前目标: {agent.current_goal || "无"}
                  </p>
                </div>
              </div>
            </section>

            {/* 人格特质 */}
            {Object.keys(personality).length > 0 && (
              <section className="mt-3 rounded-2xl border border-white/70 bg-white/80 p-4 shadow-xs backdrop-blur-sm">
                <p className="text-[11px] uppercase tracking-[0.15em] text-moss">人格特质</p>
                <div className="mt-3 space-y-2">
                  {Object.entries(personality).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-slate-600">
                        {PERSONALITY_LABELS[key] || key}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-moss"
                            style={{ width: `${(value as number) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">
                          {(value as number).toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 角色配置 */}
            {Object.keys(profile).length > 0 && (
              <section className="mt-3 rounded-2xl border border-white/70 bg-white/80 p-4 shadow-xs backdrop-blur-sm">
                <p className="text-[11px] uppercase tracking-[0.15em] text-moss">角色设定</p>
                <div className="mt-3 space-y-2">
                  {Object.entries(profile).map(([key, value]) => (
                    <div key={key}>
                      <span className="text-[10px] text-slate-400">
                        {PROFILE_LABELS[key] || key}
                      </span>
                      <p className="text-sm text-slate-700">{String(value)}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 关系网络 */}
            {relationships.length > 0 && (
              <section className="mt-3 rounded-2xl border border-white/70 bg-white/80 p-4 shadow-xs backdrop-blur-sm">
                <p className="text-[11px] uppercase tracking-[0.15em] text-moss">
                  关系网络 ({relationships.length})
                </p>
                <div className="mt-3 space-y-3">
                  {(showAllRelationships ? relationships : relationships.slice(0, 5)).map((rel: AgentRelationship, index: number) => {
                    const familiarityPct = (rel.familiarity * 100).toFixed(0);
                    const barColor = relationshipTone(rel.familiarity);
                    const textColor = rel.familiarity >= 0.75
                      ? "text-emerald-600"
                      : rel.familiarity >= 0.45
                        ? "text-amber-600"
                        : "text-slate-500";
                    return (
                      <div key={`${rel.other_agent_id}-${index}`}>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-700">{rel.other_agent_name || "未知"}</span>
                          <span className={`text-[10px] ${textColor}`}>
                            {familiarityPct}%
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${barColor}`}
                            style={{ width: `${familiarityPct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
                {relationships.length > 5 && (
                  <button
                    type="button"
                    onClick={() => setShowAllRelationships((v) => !v)}
                    className="mt-3 w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 text-xs text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
                  >
                    {showAllRelationships ? "收起" : `查看全部 ${relationships.length} 个关系`}
                  </button>
                )}
              </section>
            )}
          </div>
        </aside>

        <div className="flex min-h-0 flex-1 flex-col bg-slate-50/30 p-4">
          <AgentSignalsPanel agent={agent} world={world} compact />
        </div>
      </div>
    </Modal>
  );
}
