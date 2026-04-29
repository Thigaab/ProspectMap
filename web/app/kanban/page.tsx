import { KanbanBoard } from "@/components/kanban-board";

export default function KanbanPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Kanban</h1>
        <p className="text-sm text-zinc-500">
          Drag a card between columns to move the lead. Click the name to edit
          notes.
        </p>
      </div>
      <KanbanBoard />
    </div>
  );
}
