"use client";

import dynamic from "next/dynamic";
import { useProspects } from "@/lib/hooks";

const MapView = dynamic(() => import("@/components/map-view"), {
  ssr: false,
  loading: () => (
    <div className="h-[600px] w-full animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />
  ),
});

export default function MapPage() {
  const prospects = useProspects();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Map</h1>
        <p className="text-sm text-zinc-500">
          Pins colored by priority. Click a pin for contact info.
        </p>
      </div>
      {prospects.isLoading ? (
        <p className="text-sm text-zinc-500">Loading prospects…</p>
      ) : prospects.isError ? (
        <p className="text-sm text-red-600">
          Failed to load prospects from the API.
        </p>
      ) : (
        <MapView prospects={prospects.data ?? []} />
      )}
    </div>
  );
}
