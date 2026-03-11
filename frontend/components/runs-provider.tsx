"use client";

import { createContext, useContext, useEffect, type ReactNode } from "react";
import useSWR from "swr";
import { buildApiUrl, fetchApiResult, type ApiResult } from "@/lib/api";
import type { RunSummary } from "@/lib/types";

type RunsContextValue = {
  runs: RunSummary[];
  error: string | null;
  status: number | null;
  refreshRuns: () => Promise<ApiResult<RunSummary[]> | undefined>;
};

const RunsContext = createContext<RunsContextValue | null>(null);

type RunsProviderProps = {
  children: ReactNode;
  initialResult: ApiResult<RunSummary[]>;
};

export function RunsProvider({ children, initialResult }: RunsProviderProps) {
  const { data, mutate } = useSWR<ApiResult<RunSummary[]>>(buildApiUrl("/runs"), fetchApiResult, {
    refreshInterval: 10000,
    fallbackData: initialResult,
  });

  useEffect(() => {
    void mutate(initialResult, false);
  }, [initialResult, mutate]);

  const value: RunsContextValue = {
    runs: data?.data ?? [],
    error: data?.error ?? null,
    status: data?.status ?? null,
    refreshRuns: () => mutate(),
  };

  return <RunsContext.Provider value={value}>{children}</RunsContext.Provider>;
}

export function useRuns() {
  const context = useContext(RunsContext);
  if (!context) {
    throw new Error("useRuns must be used within a RunsProvider");
  }
  return context;
}
