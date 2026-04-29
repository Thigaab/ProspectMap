"use client";

import { useEffect, useState } from "react";
import type { Prospect } from "@/lib/types";
import { useUpdateProspect } from "@/lib/hooks";
import { Button } from "./ui/button";
import { Label, Textarea } from "./ui/field";
import { StatusBadge } from "./ui/badge";

export function NotesDialog({
  prospect,
  onClose,
}: {
  prospect: Prospect | null;
  onClose: () => void;
}) {
  const [notes, setNotes] = useState("");
  const update = useUpdateProspect();

  useEffect(() => {
    setNotes(prospect?.notes ?? "");
  }, [prospect]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (prospect) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [prospect, onClose]);

  if (!prospect) return null;

  function save() {
    if (!prospect) return;
    update.mutate(
      { placeId: prospect.place_id, notes: notes || null },
      { onSuccess: () => onClose() },
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-5 shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold">{prospect.name}</h2>
            {prospect.address && (
              <p className="text-xs text-zinc-500">{prospect.address}</p>
            )}
          </div>
          <StatusBadge value={prospect.status} />
        </div>

        <dl className="mb-4 grid grid-cols-2 gap-2 text-sm">
          <Field label="Score" value={String(prospect.score)} />
          <Field label="Priority" value={prospect.priority} />
          <Field label="Phone" value={prospect.phone ?? "—"} />
          <Field
            label="Website"
            value={prospect.website ? "Yes" : "No website"}
          />
        </dl>

        <div className="space-y-1">
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Call notes, follow-ups, contact name…"
          />
        </div>

        {update.isError && (
          <p className="mt-2 text-sm text-red-600">Failed to save notes.</p>
        )}

        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={update.isPending}>
            Cancel
          </Button>
          <Button onClick={save} disabled={update.isPending}>
            {update.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-zinc-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
