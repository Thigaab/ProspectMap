"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, Trash2 } from "lucide-react";
import type {
  LeadStatus,
  Priority,
  Prospect,
} from "@/lib/types";
import { useDeleteProspect, useProspects } from "@/lib/hooks";
import { Input, Label, Select } from "./ui/field";
import { PriorityBadge, StatusBadge } from "./ui/badge";
import { ConfirmDialog } from "./confirm-dialog";
import { cn } from "@/lib/utils";

type SortKey = "name" | "score" | "rating" | "review_count";
type SortDir = "asc" | "desc";

const PRIORITIES: ("" | Priority)[] = ["", "HIGH", "MEDIUM", "LOW"];
const STATUSES: ("" | LeadStatus)[] = [
  "",
  "NEW",
  "CONTACTED",
  "QUALIFIED",
  "WON",
  "LOST",
];

export function ProspectTable() {
  const { data, isLoading, isError } = useProspects();
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState<"" | Priority>("");
  const [status, setStatus] = useState<"" | LeadStatus>("");
  const [minScore, setMinScore] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [pendingDelete, setPendingDelete] = useState<Prospect | null>(null);
  const deleteProspect = useDeleteProspect();

  function confirmDelete() {
    if (!pendingDelete) return;
    deleteProspect.mutate(pendingDelete.place_id, {
      onSuccess: () => setPendingDelete(null),
    });
  }

  const rows = useMemo(() => {
    let r = data ?? [];
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      r = r.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.address?.toLowerCase().includes(q),
      );
    }
    if (priority) r = r.filter((p) => p.priority === priority);
    if (status) r = r.filter((p) => p.status === status);
    if (minScore > 0) r = r.filter((p) => p.score >= minScore);
    return [...r].sort((a, b) => {
      const av = pluck(a, sortKey);
      const bv = pluck(b, sortKey);
      if (av === bv) return 0;
      const cmp = av < bv ? -1 : 1;
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [data, search, priority, status, minScore, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (k === sortKey) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortKey(k);
      setSortDir(k === "name" ? "asc" : "desc");
    }
  }

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;
  if (isError)
    return <p className="text-sm text-red-600">Failed to load prospects.</p>;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_1fr]">
        <div className="space-y-1">
          <Label htmlFor="search">Search</Label>
          <Input
            id="search"
            placeholder="Name or address…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="priority">Priority</Label>
          <Select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as "" | Priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p || "All"}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="status">Status</Label>
          <Select
            id="status"
            value={status}
            onChange={(e) => setStatus(e.target.value as "" | LeadStatus)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s || "All"}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="minScore">Min score</Label>
          <Input
            id="minScore"
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value) || 0)}
          />
        </div>
      </div>

      <p className="text-xs text-zinc-500">
        {rows.length} of {data?.length ?? 0} prospect(s)
      </p>

      <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 text-left dark:bg-zinc-900">
            <tr>
              <Th onClick={() => toggleSort("name")} active={sortKey === "name"} dir={sortDir}>
                Name
              </Th>
              <th className="px-3 py-2 font-medium">Phone</th>
              <th className="px-3 py-2 font-medium">Website</th>
              <Th
                onClick={() => toggleSort("rating")}
                active={sortKey === "rating"}
                dir={sortDir}
                align="right"
              >
                Rating
              </Th>
              <Th
                onClick={() => toggleSort("review_count")}
                active={sortKey === "review_count"}
                dir={sortDir}
                align="right"
              >
                Reviews
              </Th>
              <Th
                onClick={() => toggleSort("score")}
                active={sortKey === "score"}
                dir={sortDir}
                align="right"
              >
                Score
              </Th>
              <th className="px-3 py-2 font-medium">Priority</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2" aria-label="Actions" />
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {rows.map((p) => (
              <tr
                key={p.place_id}
                className="bg-white hover:bg-zinc-50 dark:bg-zinc-950 dark:hover:bg-zinc-900"
              >
                <td className="px-3 py-2">
                  <div className="font-medium">{p.name ?? "—"}</div>
                  {p.address && (
                    <div className="text-xs text-zinc-500">{p.address}</div>
                  )}
                </td>
                <td className="px-3 py-2">{p.phone ?? "—"}</td>
                <td className="px-3 py-2">
                  {p.website ? (
                    <a
                      href={p.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 underline"
                    >
                      link
                    </a>
                  ) : (
                    <span className="text-red-600">none</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">{p.rating ?? "—"}</td>
                <td className="px-3 py-2 text-right">{p.review_count}</td>
                <td className="px-3 py-2 text-right font-semibold">
                  {p.score}
                </td>
                <td className="px-3 py-2">
                  <PriorityBadge value={p.priority} />
                </td>
                <td className="px-3 py-2">
                  <StatusBadge value={p.status} />
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => setPendingDelete(p)}
                    aria-label={`Delete ${p.name ?? "prospect"}`}
                    className="rounded-md p-1 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-6 text-center text-zinc-500"
                >
                  No prospects match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this prospect?"
        description={
          pendingDelete && (
            <p>
              <span className="font-medium">
                {pendingDelete.name ?? pendingDelete.place_id}
              </span>{" "}
              will be removed from the database, along with its notes and
              status. This cannot be undone.
            </p>
          )
        }
        confirmLabel="Delete prospect"
        pending={deleteProspect.isPending}
        error={deleteProspect.isError ? "Failed to delete." : null}
        onConfirm={confirmDelete}
        onClose={() => {
          if (!deleteProspect.isPending) setPendingDelete(null);
        }}
      />
    </div>
  );
}

function pluck(p: Prospect, k: SortKey): number | string {
  switch (k) {
    case "name":
      return (p.name ?? "").toLowerCase();
    case "score":
      return p.score;
    case "rating":
      return p.rating ?? -1;
    case "review_count":
      return p.review_count;
  }
}

function Th({
  onClick,
  active,
  dir,
  align = "left",
  children,
}: {
  onClick: () => void;
  active: boolean;
  dir: SortDir;
  align?: "left" | "right";
  children: React.ReactNode;
}) {
  const Icon = active ? (dir === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
  return (
    <th
      className={cn(
        "select-none px-3 py-2 font-medium",
        align === "right" ? "text-right" : "text-left",
      )}
    >
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100",
          align === "right" && "ml-auto",
          active ? "text-zinc-900 dark:text-zinc-100" : "text-zinc-500",
        )}
      >
        {children}
        <Icon className="h-3 w-3" />
      </button>
    </th>
  );
}
