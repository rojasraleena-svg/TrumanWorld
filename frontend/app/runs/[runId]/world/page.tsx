import Link from "next/link";

import { WorldCanvas } from "@/components/world-canvas";
import { getWorld } from "@/lib/api";

type WorldPageProps = {
  params: Promise<{ runId: string }>;
};

export default async function WorldPage({ params }: WorldPageProps) {
  const { runId } = await params;
  const initialData = await getWorld(runId);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#f7f3e8,_#eef5f1_48%,_#f8fafc)] px-6 py-12">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="space-y-3">
          <Link href={`/runs/${runId}`} className="text-sm uppercase tracking-[0.25em] text-moss">
            Director Console
          </Link>
          <h1 className="text-5xl font-semibold text-ink">
            {initialData ? initialData.run.name : "World Viewer"}
          </h1>
          <p className="max-w-3xl text-slate-600">
            小镇实况。地点、人物分布与最近的故事节拍会每 5 秒自动更新。
          </p>
        </header>

        <WorldCanvas runId={runId} initialData={initialData} />
      </div>
    </main>
  );
}
