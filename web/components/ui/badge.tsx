import { cn } from "@/lib/utils";
import type { LeadStatus, Priority } from "@/lib/types";

const PRIORITY_STYLES: Record<Priority, string> = {
  HIGH: "bg-red-100 text-red-800 dark:bg-red-950/50 dark:text-red-300",
  MEDIUM:
    "bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300",
  LOW: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
};

const STATUS_STYLES: Record<LeadStatus, string> = {
  NEW: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  CONTACTED: "bg-sky-100 text-sky-800 dark:bg-sky-950/50 dark:text-sky-300",
  QUALIFIED:
    "bg-violet-100 text-violet-800 dark:bg-violet-950/50 dark:text-violet-300",
  WON:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300",
  LOST: "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300",
};

export function PriorityBadge({ value }: { value: Priority }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        PRIORITY_STYLES[value],
      )}
    >
      {value}
    </span>
  );
}

export function StatusBadge({ value }: { value: LeadStatus }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        STATUS_STYLES[value],
      )}
    >
      {value}
    </span>
  );
}
