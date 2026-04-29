"use client";

import "leaflet/dist/leaflet.css";

import { useMemo } from "react";
import L from "leaflet";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import type { Prospect } from "@/lib/types";

const PRIORITY_COLORS = {
  HIGH: "#dc2626",
  MEDIUM: "#d97706",
  LOW: "#71717a",
} as const;

function pinIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width: 18px; height: 18px; border-radius: 50%;
      background: ${color}; border: 2px solid white;
      box-shadow: 0 0 0 1px rgba(0,0,0,.15);
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useMemo(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 15);
      return;
    }
    map.fitBounds(points, { padding: [40, 40] });
  }, [map, points]);
  return null;
}

export default function MapView({ prospects }: { prospects: Prospect[] }) {
  const geo = prospects.filter(
    (p): p is Prospect & { lat: number; lng: number } =>
      p.lat != null && p.lng != null,
  );

  const points = geo.map((p) => [p.lat, p.lng] as [number, number]);
  const center: [number, number] =
    points[0] ?? [46.603354, 1.888334]; // France centroid fallback

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm text-zinc-500">
        <span>
          {geo.length} pin(s) ·{" "}
          {prospects.length - geo.length > 0 && (
            <span className="text-amber-600">
              {prospects.length - geo.length} prospect(s) without geo data
              (re-run search with refresh to populate)
            </span>
          )}
        </span>
        <Legend />
      </div>
      <div className="h-[600px] w-full overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800">
        <MapContainer
          center={center}
          zoom={geo.length > 0 ? 13 : 6}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {geo.map((p) => (
            <Marker
              key={p.place_id}
              position={[p.lat, p.lng]}
              icon={pinIcon(PRIORITY_COLORS[p.priority])}
            >
              <Popup>
                <div className="space-y-1 text-sm">
                  <div className="font-semibold">{p.name}</div>
                  <div>
                    Score <strong>{p.score}</strong> · {p.priority}
                  </div>
                  {p.rating != null && (
                    <div>
                      ★ {p.rating} ({p.review_count})
                    </div>
                  )}
                  {p.phone && <div>{p.phone}</div>}
                  {p.website ? (
                    <a
                      href={p.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 underline"
                    >
                      Website
                    </a>
                  ) : (
                    <div className="text-red-600">No website</div>
                  )}
                  {p.google_url && (
                    <a
                      href={p.google_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-blue-600 underline"
                    >
                      Open in Google Maps
                    </a>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
          <FitBounds points={points} />
        </MapContainer>
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div className="flex items-center gap-3">
      {(["HIGH", "MEDIUM", "LOW"] as const).map((p) => (
        <span key={p} className="inline-flex items-center gap-1.5">
          <span
            className="inline-block h-3 w-3 rounded-full border border-white shadow-sm"
            style={{ background: PRIORITY_COLORS[p] }}
          />
          <span>{p}</span>
        </span>
      ))}
    </div>
  );
}
