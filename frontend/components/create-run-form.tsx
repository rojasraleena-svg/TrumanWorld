"use client";

import { useState, useTransition } from "react";

import { createRun } from "@/lib/api";

export function CreateRunForm() {
  const [name, setName] = useState("demo-run");
  const [message, setMessage] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const result = await createRun(name);
          if (result) {
            setMessage(`已创建 run：${result.name} (${result.id})`);
          } else {
            setMessage("创建失败，可能是后端未启动。");
          }
        });
      }}
    >
      <label className="block space-y-2">
        <span className="text-sm font-medium text-ink">Run Name</span>
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-0 transition focus:border-moss"
          placeholder="输入新的 run 名称"
        />
      </label>
      <button
        type="submit"
        disabled={isPending}
        className="inline-flex rounded-full bg-ink px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {isPending ? "Creating..." : "Create Run"}
      </button>
      {message ? <p className="text-sm text-slate-600">{message}</p> : null}
    </form>
  );
}

