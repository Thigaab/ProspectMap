export type Priority = "HIGH" | "MEDIUM" | "LOW";
export type LeadStatus = "NEW" | "CONTACTED" | "QUALIFIED" | "WON" | "LOST";

export type Prospect = {
  place_id: string;
  name: string | null;
  address: string | null;
  phone: string | null;
  website: string | null;
  rating: number | null;
  review_count: number;
  score: number;
  priority: Priority;
  reasons: string[];
  google_url: string | null;
  types: string[];
  hours: string[];
  lat: number | null;
  lng: number | null;
  status: LeadStatus;
  notes: string | null;
  updated_at: string | null;
};

export type CachedSearch = {
  city: string;
  type_filter: string;
  radius: number;
  fetched_at: string;
  prospect_count: number;
};

export type SearchRequest = {
  city: string;
  type_filter?: string;
  radius?: number;
  refresh?: boolean;
  ttl_days?: number;
};

export type SearchResponse = {
  cached: boolean;
  fetched_at: string;
  prospects: Prospect[];
};

export type ProspectFilters = {
  status?: LeadStatus;
  priority?: Priority;
  min_score?: number;
};
