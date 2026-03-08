"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { deleteRun } from "@/lib/api";

type Run = {
  id: string;
  name: string;
  status: string;
  current_tick?: number;
  was_running_before_restart?: boolean;
};

type RunListProps = {
  runs: Run[];
};

export function RunList({ runs }: RunListProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = (runId: string) => {
    if (!confirm("确定要删除这个模拟运行吗？此操作不可撤销。")) {
      return;
    }

    setDeletingId(runId);
    startTransition(async () => {
      const result = await deleteRun(runId);
      if (result) {
        router.refresh();
      } else {
        alert("删除失败，请重试。");
      }
      setDeletingId(null);
    });
  };

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-[28px] border border-dashed border-slate-200 bg-white py-16 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-50">
          <svg className="h-8 w-8 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <p className="mt-4 text-sm font-medium text-slate-600">还没有运行</p>
        <p className="mt-1 text-xs text-slate-400">在上方创建第一个模拟运行</p>
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {runs.map((run) => {
        const isRunning = run.status === "running";
        const isPaused = run.status === "paused";
        return (
          <div
            key={run.id}
            className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-moss/50 hover:shadow-md"
          >
            {/* 名称行：名称 + 状态点 + 删除 */}
            <div className="flex items-center gap-2">
              <Link href={`/runs/${run.id}`} className="min-w-0 flex-1">
                <h3 className="truncate text-base font-semibold text-ink transition-colors group-hover:text-moss">
                  {run.name}
                </h3>
              </Link>
              <div
                className={`h-2 w-2 flex-shrink-0 rounded-full ${
                  isRunning
                    ? "animate-pulse bg-emerald-500"
                    : isPaused
                    ? "bg-amber-400"
                    : "bg-slate-300"
                }`}
              />
              <button
                type="button"
                onClick={() => handleDelete(run.id)}
                disabled={isPending && deletingId === run.id}
                className="flex-shrink-0 rounded-full p-1 text-slate-300 transition hover:bg-red-50 hover:text-red-400 disabled:opacity-50"
                title="删除"
              >
                {deletingId === run.id ? (
                  <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-200 border-t-red-400" />
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18" />
                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                )}
              </button>
            </div>

            <p className="mt-0.5 text-[11px] text-slate-400">ID {run.id.slice(0, 8)}...</p>

            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                    isRunning
                      ? "bg-emerald-50 text-emerald-700"
                      : isPaused
                      ? "bg-amber-50 text-amber-700"
                      : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {isRunning ? "运行中" : isPaused ? "已暂停" : run.status}
                </span>
                {run.was_running_before_restart && (
                  <span className="rounded-full bg-orange-50 px-1.5 py-0.5 text-[10px] font-medium text-orange-600">
                    待恢复
                  </span>
                )}
              </div>
              <span className="text-[11px] text-slate-400">
                T<span className="font-semibold text-slate-600">{run.current_tick ?? 0}</span>
              </span>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-1.5">
              <Link
                href={`/runs/${run.id}`}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-center text-xs font-medium text-ink transition hover:border-moss hover:bg-moss/5 hover:text-moss"
              >
                总览
              </Link>
              <Link
                href={`/runs/${run.id}/world`}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-center text-xs font-medium text-slate-600 transition hover:border-moss hover:text-moss"
              >
                世界视图
              </Link>
            </div>
          </div>
        );
      })}
    </div>
  );
}
