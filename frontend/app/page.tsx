import { CreateRunForm } from "@/components/create-run-form";
import { RestoreBanner } from "@/components/restore-banner";
import { RunList } from "@/components/run-list";
import { DeleteAllButton } from "@/components/delete-all-button";
import { listRuns } from "@/lib/api";

export default async function HomePage() {
  const runs = await listRuns();
  const hasRuns = runs.length > 0;
  const runningCount = runs.filter((r) => r.status === "running").length;
  const needsRestoreCount = runs.filter((r) => r.was_running_before_restart).length;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* 顶部 header */}
      <div className="flex-shrink-0 border-b border-slate-200/60 bg-white px-8 py-5">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-ink">控制台</h1>
          {hasRuns && (
            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              <span className="text-xs font-medium text-slate-600">{runningCount} 个运行中</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-8 space-y-8">
          {needsRestoreCount > 0 && <RestoreBanner count={needsRestoreCount} />}

          {/* 创建新模拟 */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-4">
              <h2 className="text-sm font-semibold text-slate-500 whitespace-nowrap">创建运行</h2>
              <div className="flex-1">
                <CreateRunForm />
              </div>
            </div>
          </section>

          {/* 运行列表 */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-ink">模拟运行</h2>
                {hasRuns && (
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
                    {runs.length}
                  </span>
                )}
              </div>
              {runs.length > 1 && <DeleteAllButton runs={runs} />}
            </div>
            <RunList runs={runs} />
          </section>
        </div>
      </div>
    </div>
  );
}

