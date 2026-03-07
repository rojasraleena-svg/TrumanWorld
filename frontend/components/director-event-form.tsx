"use client";

import { useState, useTransition } from "react";

import { injectDirectorEvent } from "@/lib/api";

type DirectorEventFormProps = {
  runId: string;
};

export function DirectorEventForm({ runId }: DirectorEventFormProps) {
  const [eventType, setEventType] = useState("broadcast");
  const [message, setMessage] = useState("Town hall at plaza");
  const [statusMessage, setStatusMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(async () => {
          const result = await injectDirectorEvent(runId, {
            event_type: eventType,
            payload: { message },
            importance: 0.8,
          });
          setStatusMessage(result ? "事件已注入，请刷新 timeline 查看。" : "注入失败，可能是后端未启动。");
        });
      }}
    >
      <label className="block space-y-2">
        <span className="text-sm font-medium text-ink">Event Type</span>
        <input
          value={eventType}
          onChange={(event) => setEventType(event.target.value)}
          className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-moss"
        />
      </label>
      <label className="block space-y-2">
        <span className="text-sm font-medium text-ink">Message</span>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          className="min-h-28 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-moss"
        />
      </label>
      <button
        type="submit"
        disabled={isPending}
        className="inline-flex rounded-full bg-ember px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {isPending ? "Injecting..." : "Inject Event"}
      </button>
      {statusMessage ? <p className="text-sm text-slate-600">{statusMessage}</p> : null}
    </form>
  );
}

