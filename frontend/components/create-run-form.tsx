"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { createRun } from "@/lib/api";

export function CreateRunForm() {
  const router = useRouter();
  const [name, setName] = useState("demo-run");
  const [seedDemo, setSeedDemo] = useState(true);
  const [message, setMessage] = useState<string>("");
  const [isPending, startTransition] = useTransition();
  const suggestions = ["demo-run", "town-morning", "story-lab", "night-shift"];

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const result = await createRun(name, seedDemo);
          if (result) {
            setMessage(`已创建：${result.name}`);
            router.push(`/runs/${result.id}`);
            router.refresh();
          } else {
            setMessage("创建失败，后端可能未启动");
          }
        });
      }}
    >
      {/* 名称输入行 */}
      <div className="flex items-center gap-3">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-ink placeholder:text-slate-400 outline-none transition focus:border-moss focus:bg-white focus:ring-2 focus:ring-moss/20"
          placeholder="输入模拟运行名称"
        />
        <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 transition hover:border-moss/50 hover:bg-white">
          <input
            type="checkbox"
            checked={seedDemo}
            onChange={(event) => setSeedDemo(event.target.checked)}
            className="h-3.5 w-3.5 rounded border-slate-300 text-moss focus:ring-moss"
          />
          <span className="text-xs font-medium text-slate-600 whitespace-nowrap">Demo World</span>
        </label>
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex items-center gap-2 rounded-xl bg-moss px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-moss/90 disabled:opacity-60 whitespace-nowrap"
        >
          {isPending ? (
            <>
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              创建中...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              创建运行
            </>
          )}
        </button>
      </div>

      {/* 推荐命名 */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400">推荐：</span>
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setName(suggestion)}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-500 transition hover:border-moss hover:text-moss"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {message && (
        <p
          className={`rounded-xl border px-4 py-3 text-sm ${
            message.includes("失败")
              ? "border-red-200 bg-red-50 text-red-700"
              : "border-emerald-200 bg-emerald-50 text-emerald-700"
          }`}
        >
          {message}
        </p>
      )}
    </form>
  );
}
