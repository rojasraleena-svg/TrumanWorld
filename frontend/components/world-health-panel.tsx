"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import type {
  WorldHealthMetrics,
  Trend,
} from "@/lib/world-insights";
import {
  getTrendIcon,
  getTrendColor,
  getScoreColor,
  getScoreBgColor,
} from "@/lib/world-insights";
import { DirectorEventForm } from "@/components/director-event-form";

interface WorldHealthPanelProps {
  metrics: WorldHealthMetrics;
  runId: string;
}

export function WorldHealthPanel({ metrics, runId }: WorldHealthPanelProps) {
  const [isDirectorExpanded, setIsDirectorExpanded] = useState(false);
  return (
    <div className="rounded-[28px] border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ink">🌍 世界健康度</h2>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-100 bg-emerald-50 px-2 py-0.5 text-[11px] text-emerald-600">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          实时
        </span>
      </div>

      <div className="mt-4 space-y-4">
        {/* 剧情连贯性 */}
        <MetricBar
          label="剧情连贯性"
          value={metrics.continuityScore}
          trend={metrics.continuityTrend}
          warning={metrics.continuityIssue}
          description="世界运行的流畅程度"
        />

        {/* 社交活跃度 */}
        <MetricBar
          label="社交活跃度"
          value={metrics.socialActivity}
          trend={metrics.socialTrend}
          suggestion={
            metrics.socialActivity < 30
              ? "居民互动较少，建议增加对话"
              : undefined
          }
          description="居民之间的交流频率"
        />

        {/* Truman怀疑度 */}
        <MetricBar
          label="Truman怀疑度"
          value={metrics.trumanSuspicion}
          trend={metrics.suspicionTrend}
          description="Truman 对世界的信任程度"
        />

        {/* 导演干预状态 */}
        <DirectorStats
          stats={metrics.directorStats}
          onClick={() => setIsDirectorExpanded(true)}
        />

        {/* 导演干预详情弹窗 */}
        <DirectorInterventionModal
          isOpen={isDirectorExpanded}
          onClose={() => setIsDirectorExpanded(false)}
          stats={metrics.directorStats}
          runId={runId}
        />
      </div>

      {/* 活动摘要 */}
      <ActivitySummary summary={metrics.activitySummary} />

      {/* 今日统计 */}
      <DailyStats
        talkCount={metrics.recentTalkCount}
        moveCount={metrics.recentMoveCount}
        rejectionCount={metrics.recentRejectionCount}
      />
    </div>
  );
}

// ============================================================================
// 指标条组件
// ============================================================================

interface MetricBarProps {
  label: string;
  value: number;
  trend: Trend;
  warning?: string;
  suggestion?: string;
  description?: string;
}

function MetricBar({
  label,
  value,
  trend,
  warning,
  suggestion,
  description,
}: MetricBarProps) {
  const scoreColor = getScoreColor(value);
  const scoreBgColor = getScoreBgColor(value);
  const trendIcon = getTrendIcon(trend);
  const trendColor = getTrendColor(trend);

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700">{label}</span>
          {description && (
            <Tooltip text={description} />
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-semibold ${scoreColor}`}>
            {value}%
          </span>
          <span className={`text-xs ${trendColor}`}>{trendIcon}</span>
        </div>
      </div>

      {/* 进度条 */}
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className={`h-full rounded-full ${scoreBgColor}`}
        />
      </div>

      {/* 警告或建议 */}
      {warning && (
        <div className="flex items-start gap-1.5 text-xs text-amber-600">
          <span>⚠️</span>
          <span>{warning}</span>
        </div>
      )}
      {suggestion && !warning && (
        <div className="flex items-start gap-1.5 text-xs text-blue-600">
          <span>💡</span>
          <span>{suggestion}</span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 导演统计组件
// ============================================================================

interface DirectorStatsProps {
  stats: {
    total: number;
    executed: number;
    executionRate: number;
  };
  onClick?: () => void;
}

function DirectorStats({ stats, onClick }: DirectorStatsProps) {
  const hasIssue = stats.executionRate < 50 && stats.total > 0;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-xl bg-slate-50 p-3 text-left transition hover:bg-slate-100"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700">🎬 导演干预</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-medium ${
              hasIssue ? "text-amber-600" : "text-slate-500"
            }`}
          >
            {stats.executionRate}% 执行率
          </span>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="h-4 w-4 text-slate-400"
          >
            <path d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-semibold text-slate-800">
            {stats.total}
          </span>
          <span className="text-xs text-slate-500">计划</span>
        </div>
        <div className="h-4 w-px bg-slate-200" />
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-semibold text-emerald-600">
            {stats.executed}
          </span>
          <span className="text-xs text-slate-500">已执行</span>
        </div>
        <div className="h-4 w-px bg-slate-200" />
        <div className="flex items-center gap-1.5">
          <span
            className={`text-lg font-semibold ${
              hasIssue ? "text-amber-600" : "text-slate-600"
            }`}
          >
            {stats.total - stats.executed}
          </span>
          <span className="text-xs text-slate-500">待执行</span>
        </div>
      </div>

      {hasIssue && (
        <div className="mt-2 flex items-start gap-1.5 text-xs text-amber-600">
          <span>⚠️</span>
          <span>干预执行率较低，建议检查干预传递流程</span>
        </div>
      )}
    </button>
  );
}

// ============================================================================
// 活动摘要组件
// ============================================================================

interface ActivitySummaryProps {
  summary: {
    working: number;
    resting: number;
    commuting: number;
    total: number;
  };
}

function ActivitySummary({ summary }: ActivitySummaryProps) {
  return (
    <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50/50 p-3">
      <div className="text-xs font-medium text-slate-500">当前活动分布</div>
      <div className="mt-2 flex items-center justify-between">
        <ActivityBadge
          icon="⚒️"
          label="在岗中"
          count={summary.working}
          color="amber"
        />
        <ActivityBadge
          icon="😴"
          label="休息中"
          count={summary.resting}
          color="slate"
        />
        <ActivityBadge
          icon="🚶"
          label="通勤中"
          count={summary.commuting}
          color="blue"
        />
      </div>
    </div>
  );
}

interface ActivityBadgeProps {
  icon: string;
  label: string;
  count: number;
  color: "amber" | "slate" | "blue";
}

function ActivityBadge({ icon, label, count, color }: ActivityBadgeProps) {
  const colorClasses = {
    amber: "bg-amber-50 text-amber-700 border-amber-100",
    slate: "bg-slate-50 text-slate-700 border-slate-100",
    blue: "bg-blue-50 text-blue-700 border-blue-100",
  };

  return (
    <div
      className={`flex flex-col items-center rounded-lg border px-3 py-2 ${colorClasses[color]}`}
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-semibold">{count}</span>
      <span className="text-[10px] text-slate-500">{label}</span>
    </div>
  );
}

// ============================================================================
// 今日统计组件
// ============================================================================

interface DailyStatsProps {
  talkCount: number;
  moveCount: number;
  rejectionCount: number;
}

function DailyStats({
  talkCount,
  moveCount,
  rejectionCount,
}: DailyStatsProps) {
  return (
    <div className="mt-4 grid grid-cols-3 gap-2">
      <StatItem icon="💬" value={talkCount} label="对话" />
      <StatItem icon="🚶" value={moveCount} label="移动" />
      <StatItem
        icon="⚠️"
        value={rejectionCount}
        label="异常"
        highlight={rejectionCount > 0}
      />
    </div>
  );
}

interface StatItemProps {
  icon: string;
  value: number;
  label: string;
  highlight?: boolean;
}

function StatItem({ icon, value, label, highlight }: StatItemProps) {
  return (
    <div
      className={`flex flex-col items-center rounded-xl px-2 py-2 ${
        highlight
          ? "bg-amber-50 border border-amber-100"
          : "bg-slate-50"
      }`}
    >
      <span className="text-base">{icon}</span>
      <span
        className={`text-sm font-semibold ${
          highlight ? "text-amber-700" : "text-slate-700"
        }`}
      >
        {value}
      </span>
      <span className="text-[10px] text-slate-500">{label}</span>
    </div>
  );
}

// ============================================================================
// 导演干预详情弹窗
// ============================================================================

interface DirectorInterventionModalProps {
  isOpen: boolean;
  onClose: () => void;
  stats: {
    total: number;
    executed: number;
    executionRate: number;
  };
  runId: string;
}

function DirectorInterventionModal({ isOpen, onClose, stats, runId }: DirectorInterventionModalProps) {
  const pendingCount = stats.total - stats.executed;
  const hasIssue = stats.executionRate < 50 && stats.total > 0;

  const modal = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-6 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.93, opacity: 0, y: 16 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.93, opacity: 0, y: 16 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 头部 */}
            <div className="flex items-start justify-between border-b border-slate-100 px-7 py-5">
              <div>
                <h2 className="text-xl font-semibold text-ink">🎬 导演干预控制台</h2>
                <p className="mt-0.5 text-sm text-slate-400">管理和监控所有导演干预计划</p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 主体：左右两列 */}
            <div className="flex min-h-0 flex-1 overflow-hidden">
              {/* 左侧：统计 + 执行率 */}
              <div className="flex w-64 shrink-0 flex-col gap-5 border-r border-slate-100 bg-slate-50/60 px-6 py-6">
                {/* 统计三格 */}
                <div className="space-y-3">
                  <StatCard label="计划干预" value={stats.total} icon="📋" color="slate" />
                  <StatCard label="已执行" value={stats.executed} icon="✅" color="emerald" />
                  <StatCard label="待执行" value={pendingCount} icon="⏳" color={hasIssue ? "amber" : "slate"} />
                </div>

                {/* 执行率 */}
                <div className="rounded-2xl bg-white p-5 shadow-sm">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">执行率</span>
                    <span className={`font-bold ${hasIssue ? "text-amber-600" : "text-emerald-600"}`}>
                      {stats.executionRate}%
                    </span>
                  </div>
                  <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${stats.executionRate}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full rounded-full ${hasIssue ? "bg-amber-500" : "bg-emerald-500"}`}
                    />
                  </div>
                  {hasIssue && (
                    <p className="mt-3 text-xs text-amber-600">⚠️ 执行率较低</p>
                  )}
                </div>
              </div>

              {/* 右侧：导演干预表单 */}
              <div className="flex-1 overflow-auto px-8 py-6">
                <DirectorEventForm runId={runId} />
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  if (typeof document === "undefined") return null;
  return createPortal(modal, document.body);
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: string;
  color: "slate" | "emerald" | "amber";
}) {
  const colorClasses = {
    slate: "bg-slate-100 text-slate-700",
    emerald: "bg-emerald-100 text-emerald-700",
    amber: "bg-amber-100 text-amber-700",
  };

  return (
    <div className={`flex items-center gap-3 rounded-xl p-3 ${colorClasses[color]}`}>
      <span className="text-2xl">{icon}</span>
      <div className="min-w-0">
        <p className="text-2xl font-bold leading-none">{value}</p>
        <p className="mt-0.5 text-xs opacity-70">{label}</p>
      </div>
    </div>
  );
}

// ============================================================================
// Tooltip 组件
// ============================================================================

function Tooltip({ text }: { text: string }) {
  return (
    <div className="group relative">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="h-3.5 w-3.5 cursor-help text-slate-400"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div className="absolute left-5 top-1/2 z-10 hidden -translate-y-1/2 whitespace-nowrap rounded-lg bg-slate-800 px-2 py-1 text-xs text-white shadow-lg group-hover:block">
        {text}
      </div>
    </div>
  );
}
