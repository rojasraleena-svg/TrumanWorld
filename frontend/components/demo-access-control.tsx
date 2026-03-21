"use client";

import { useState, useTransition, useRef, useEffect } from "react";

import { useDemoAccess } from "@/components/demo-access-provider";

export function DemoAccessControl() {
  const { ready, writeProtected, adminAuthorized, unlock, lock } = useDemoAccess();
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    if (!open) return;
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  // 判断当前状态颜色
  const dotColor = !ready
    ? "bg-slate-300"
    : !writeProtected || adminAuthorized
    ? "bg-emerald-400"
    : "bg-amber-400";

  const dotTitle = !ready
    ? "权限检查中"
    : !writeProtected || adminAuthorized
    ? "可编辑模式"
    : "只读 Demo 模式";

  return (
    <div ref={ref} className="relative">
      {/* 小圆点触发按钮 */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title={dotTitle}
        className="flex h-3 w-3 items-center justify-center rounded-full transition-transform hover:scale-125 focus:outline-none"
      >
        <span className={`block h-3 w-3 rounded-full shadow-sm ${dotColor} opacity-80 hover:opacity-100`} />
      </button>

      {/* 弹出浮层 */}
      {open && (
        <div className="absolute right-0 top-6 z-50 min-w-[200px] rounded-xl border border-white/60 bg-white/90 p-3 shadow-lg shadow-slate-900/10 backdrop-blur-md">
          {!ready && (
            <p className="text-xs text-slate-400">权限检查中…</p>
          )}

          {ready && !writeProtected && (
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-medium text-emerald-700">可编辑模式</span>
            </div>
          )}

          {ready && writeProtected && adminAuthorized && (
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-medium text-emerald-700">管理员已解锁</span>
              </div>
              <button
                type="button"
                onClick={() => { lock(); setOpen(false); }}
                className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600 transition hover:border-slate-300 hover:text-slate-800"
              >
                锁定
              </button>
            </div>
          )}

          {ready && writeProtected && !adminAuthorized && (
            <form
              className="flex flex-col gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                setMessage("");
                startTransition(async () => {
                  const result = await unlock(password);
                  if (result.ok) {
                    setPassword("");
                    setOpen(false);
                    return;
                  }
                  setMessage(result.error ?? "解锁失败");
                });
              }}
            >
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                <span className="text-xs font-medium text-amber-700">只读 Demo</span>
              </div>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="管理员密码"
                className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 outline-hidden transition focus:border-moss focus:ring-2 focus:ring-moss/20"
              />
              <button
                type="submit"
                disabled={isPending || password.trim().length === 0}
                className="w-full rounded-lg bg-slate-900 py-1.5 text-xs font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                解锁控制
              </button>
              {message ? <span className="text-xs text-red-500">{message}</span> : null}
            </form>
          )}
        </div>
      )}
    </div>
  );
}
