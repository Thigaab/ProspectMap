"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useDeleteSearch, useProspects, useSearches } from "@/lib/hooks";
import { SearchForm } from "@/components/search-form";
import { ConfirmDialog } from "@/components/confirm-dialog";
import type { CachedSearch } from "@/lib/types";

export default function Dashboard() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    retry: false,
  });
  const prospects = useProspects();
  const searches = useSearches();
  const deleteSearch = useDeleteSearch();
  const [pendingDelete, setPendingDelete] = useState<CachedSearch | null>(null);

  const counts = countByPriority(prospects.data ?? []);

  function confirmDelete() {
    if (!pendingDelete) return;
    deleteSearch.mutate(pendingDelete.id, {
      onSuccess: () => setPendingDelete(null),
    });
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-zinc-500">
          Trigger a new search or browse what's already cached.
        </p>
      </div>

      <BackendStatus
        ok={health.isSuccess}
        loading={health.isLoading}
        error={health.error}
      />

      {health.isSuccess && <SearchForm />}

      <section className="grid gap-4 sm:grid-cols-3">
        <Card label="HIGH priority" value={counts.HIGH} accent="text-red-600" />
        <Card
          label="MEDIUM priority"
          value={counts.MEDIUM}
          accent="text-amber-600"
        />
        <Card label="LOW priority" value={counts.LOW} accent="text-zinc-500" />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500">
          Cached searches
        </h2>
        {searches.isLoading ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : searches.data && searches.data.length > 0 ? (
          <ul className="divide-y divide-zinc-200 rounded-md border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
            {searches.data.map((s) => (
              <li
                key={s.id}
                className="flex items-center justify-between px-4 py-3 text-sm"
              >
                <div>
                  <span className="font-medium">{s.city}</span>{" "}
                  <span className="text-zinc-500">
                    · {s.type_filter} · {s.radius}m
                  </span>
                </div>
                <div className="flex items-center gap-3 text-zinc-500">
                  <span>
                    {s.prospect_count} prospects ·{" "}
                    {new Date(s.fetched_at).toLocaleDateString()}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPendingDelete(s)}
                    aria-label={`Delete search for ${s.city}`}
                    className="rounded-md p-1 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-zinc-500">No cached searches yet.</p>
        )}
      </section>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this search?"
        description={
          pendingDelete && (
            <p>
              <span className="font-medium">{pendingDelete.city}</span>
              {" · "}
              {pendingDelete.type_filter} · {pendingDelete.radius}m. This will
              also remove its{" "}
              <span className="font-medium">
                {pendingDelete.prospect_count} prospect(s)
              </span>{" "}
              from the database (including any notes and statuses).
            </p>
          )
        }
        confirmLabel="Delete search"
        pending={deleteSearch.isPending}
        error={deleteSearch.isError ? "Failed to delete." : null}
        onConfirm={confirmDelete}
        onClose={() => {
          if (!deleteSearch.isPending) setPendingDelete(null);
        }}
      />
    </div>
  );
}

function countByPriority(prospects: { priority: string }[]) {
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0 } as Record<string, number>;
  for (const p of prospects) counts[p.priority] = (counts[p.priority] ?? 0) + 1;
  return counts;
}

function Card({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-xs uppercase tracking-wide text-zinc-500">{label}</p>
      <p className={`mt-1 text-3xl font-semibold ${accent}`}>{value}</p>
    </div>
  );
}

function BackendStatus({
  ok,
  loading,
  error,
}: {
  ok: boolean;
  loading: boolean;
  error: unknown;
}) {
  if (loading) {
    return <p className="text-sm text-zinc-500">Pinging backend…</p>;
  }
  if (ok) {
    return (
      <p className="text-sm text-emerald-600">✓ Backend reachable.</p>
    );
  }
  return (
    <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
      <p className="font-medium">Backend unreachable.</p>
      <p className="mt-1">
        Start it with{" "}
        <code className="rounded bg-red-100 px-1 py-0.5 dark:bg-red-900/50">
          uvicorn api.main:app --reload --port 8000
        </code>
        {error instanceof Error && (
          <span className="mt-1 block text-xs opacity-80">{error.message}</span>
        )}
      </p>
    </div>
  );
}
