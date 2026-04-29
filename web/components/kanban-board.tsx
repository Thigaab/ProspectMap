"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { LeadStatus, Prospect } from "@/lib/types";
import { useProspects, useUpdateProspect } from "@/lib/hooks";
import { PriorityBadge } from "./ui/badge";
import { NotesDialog } from "./notes-dialog";
import { cn } from "@/lib/utils";

const COLUMNS: { id: LeadStatus; label: string; tint: string }[] = [
  { id: "NEW", label: "New", tint: "border-zinc-300 dark:border-zinc-700" },
  {
    id: "CONTACTED",
    label: "Contacted",
    tint: "border-sky-300 dark:border-sky-800",
  },
  {
    id: "QUALIFIED",
    label: "Qualified",
    tint: "border-violet-300 dark:border-violet-800",
  },
  {
    id: "WON",
    label: "Won",
    tint: "border-emerald-300 dark:border-emerald-800",
  },
  { id: "LOST", label: "Lost", tint: "border-rose-300 dark:border-rose-800" },
];

export function KanbanBoard() {
  const prospects = useProspects();
  const update = useUpdateProspect();
  const [openProspect, setOpenProspect] = useState<Prospect | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  const grouped = useMemo(() => {
    const g: Record<LeadStatus, Prospect[]> = {
      NEW: [],
      CONTACTED: [],
      QUALIFIED: [],
      WON: [],
      LOST: [],
    };
    for (const p of prospects.data ?? []) g[p.status].push(p);
    for (const list of Object.values(g)) {
      list.sort((a, b) => b.score - a.score);
    }
    return g;
  }, [prospects.data]);

  function onDragEnd(e: DragEndEvent) {
    const { active, over } = e;
    if (!over) return;
    const placeId = String(active.id);
    const newStatus = over.id as LeadStatus;
    const current = (prospects.data ?? []).find((p) => p.place_id === placeId);
    if (!current || current.status === newStatus) return;
    update.mutate({ placeId, status: newStatus });
  }

  if (prospects.isLoading)
    return <p className="text-sm text-zinc-500">Loading…</p>;
  if (prospects.isError)
    return <p className="text-sm text-red-600">Failed to load prospects.</p>;

  return (
    <>
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
          {COLUMNS.map((col) => (
            <Column
              key={col.id}
              id={col.id}
              label={col.label}
              tint={col.tint}
              cards={grouped[col.id]}
              onCardClick={setOpenProspect}
            />
          ))}
        </div>
      </DndContext>
      <NotesDialog
        prospect={openProspect}
        onClose={() => setOpenProspect(null)}
      />
    </>
  );
}

function Column({
  id,
  label,
  tint,
  cards,
  onCardClick,
}: {
  id: LeadStatus;
  label: string;
  tint: string;
  cards: Prospect[];
  onCardClick: (p: Prospect) => void;
}) {
  const { isOver, setNodeRef } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex h-[600px] flex-col rounded-lg border-2 border-dashed bg-zinc-50 transition-colors dark:bg-zinc-900",
        tint,
        isOver && "bg-zinc-100 dark:bg-zinc-800",
      )}
    >
      <div className="flex items-center justify-between border-b border-zinc-200 px-3 py-2 dark:border-zinc-800">
        <span className="text-sm font-medium uppercase tracking-wide">
          {label}
        </span>
        <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-xs dark:bg-zinc-800">
          {cards.length}
        </span>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-2">
        {cards.map((c) => (
          <Card key={c.place_id} prospect={c} onClick={() => onCardClick(c)} />
        ))}
        {cards.length === 0 && (
          <p className="px-1 py-4 text-center text-xs text-zinc-400">
            Drop a card here
          </p>
        )}
      </div>
    </div>
  );
}

function Card({
  prospect,
  onClick,
}: {
  prospect: Prospect;
  onClick: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: prospect.place_id });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "cursor-grab rounded-md border border-zinc-200 bg-white p-2 shadow-sm dark:border-zinc-700 dark:bg-zinc-950",
        isDragging && "ring-2 ring-zinc-400",
      )}
      {...listeners}
      {...attributes}
    >
      <div className="flex items-start justify-between gap-2">
        <button
          type="button"
          onPointerDown={(e) => e.stopPropagation()}
          onClick={onClick}
          className="flex-1 cursor-pointer text-left text-sm font-medium hover:underline"
        >
          {prospect.name ?? "—"}
        </button>
        <PriorityBadge value={prospect.priority} />
      </div>
      <div className="mt-1 flex items-center justify-between text-xs text-zinc-500">
        <span>Score {prospect.score}</span>
        {prospect.phone && <span className="truncate">{prospect.phone}</span>}
      </div>
      {prospect.notes && (
        <p className="mt-1 line-clamp-2 text-xs text-zinc-600 dark:text-zinc-400">
          {prospect.notes}
        </p>
      )}
    </div>
  );
}
