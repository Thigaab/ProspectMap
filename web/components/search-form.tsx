"use client";

import { FormEvent, useState } from "react";
import { useCreateSearch } from "@/lib/hooks";
import { Button } from "./ui/button";
import { Input, Label, Select } from "./ui/field";

const TYPES = ["all", "restaurant", "bar", "retail", "services"] as const;

export function SearchForm() {
  const [city, setCity] = useState("");
  const [type, setType] = useState<(typeof TYPES)[number]>("all");
  const [radius, setRadius] = useState(2000);
  const [refresh, setRefresh] = useState(false);

  const search = useCreateSearch();

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!city.trim()) return;
    search.mutate({ city: city.trim(), type_filter: type, radius, refresh });
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end">
        <div className="space-y-1">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            placeholder="Cugnaux 31270"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            required
            disabled={search.isPending}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="type">Type</Label>
          <Select
            id="type"
            value={type}
            onChange={(e) => setType(e.target.value as typeof type)}
            disabled={search.isPending}
          >
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="radius">Radius (m)</Label>
          <Input
            id="radius"
            type="number"
            min={100}
            step={100}
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value) || 0)}
            disabled={search.isPending}
          />
        </div>
        <Button type="submit" disabled={search.isPending || !city.trim()}>
          {search.isPending ? "Searching…" : "Search"}
        </Button>
      </div>
      <label className="mt-3 inline-flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
        <input
          type="checkbox"
          checked={refresh}
          onChange={(e) => setRefresh(e.target.checked)}
          disabled={search.isPending}
        />
        Force refresh (bypass cache, re-call Google)
      </label>

      {search.isPending && (
        <p className="mt-3 text-sm text-zinc-500">
          Querying Google Places — this can take 20–30s on a cache miss.
        </p>
      )}
      {search.isSuccess && (
        <p className="mt-3 text-sm text-emerald-600">
          {search.data.cached ? "Cache hit" : "Fresh fetch"} ·{" "}
          {search.data.prospects.length} prospect(s) loaded.
        </p>
      )}
      {search.isError && (
        <p className="mt-3 text-sm text-red-600">
          {search.error instanceof Error
            ? search.error.message
            : "Search failed."}
        </p>
      )}
    </form>
  );
}
