"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./api";
import type {
  LeadStatus,
  Prospect,
  ProspectFilters,
  SearchRequest,
} from "./types";

const PROSPECTS_KEY = ["prospects"] as const;
const SEARCHES_KEY = ["searches"] as const;

export function useProspects(filters: ProspectFilters = {}) {
  return useQuery({
    queryKey: [...PROSPECTS_KEY, filters],
    queryFn: () => api.listProspects(filters),
  });
}

export function useSearches() {
  return useQuery({
    queryKey: SEARCHES_KEY,
    queryFn: api.listSearches,
  });
}

export function useCreateSearch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: SearchRequest) => api.createSearch(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PROSPECTS_KEY });
      qc.invalidateQueries({ queryKey: SEARCHES_KEY });
    },
  });
}

export function useDeleteProspect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (placeId: string) => api.deleteProspect(placeId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PROSPECTS_KEY });
      qc.invalidateQueries({ queryKey: SEARCHES_KEY });
    },
  });
}

export function useDeleteSearch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (searchId: number) => api.deleteSearch(searchId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PROSPECTS_KEY });
      qc.invalidateQueries({ queryKey: SEARCHES_KEY });
    },
  });
}

export function useUpdateProspect() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      placeId: string;
      status?: LeadStatus;
      notes?: string | null;
    }) =>
      api.updateProspect(vars.placeId, {
        status: vars.status,
        notes: vars.notes,
      }),
    onMutate: async (vars) => {
      // Optimistic update across every cached prospects query
      await qc.cancelQueries({ queryKey: PROSPECTS_KEY });
      const snapshots = qc.getQueriesData<Prospect[]>({ queryKey: PROSPECTS_KEY });
      for (const [key, data] of snapshots) {
        if (!data) continue;
        qc.setQueryData<Prospect[]>(
          key,
          data.map((p) =>
            p.place_id === vars.placeId
              ? {
                  ...p,
                  status: vars.status ?? p.status,
                  notes: vars.notes !== undefined ? vars.notes : p.notes,
                }
              : p,
          ),
        );
      }
      return { snapshots };
    },
    onError: (_err, _vars, ctx) => {
      // Rollback on failure
      if (!ctx) return;
      for (const [key, data] of ctx.snapshots) {
        qc.setQueryData(key, data);
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: PROSPECTS_KEY });
    },
  });
}
