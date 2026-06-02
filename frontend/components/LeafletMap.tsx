'use client';

import { useEffect, useMemo } from 'react';
import Link from 'next/link';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MapPin } from 'lucide-react';
import type { Property } from '@/lib/types';
import 'leaflet/dist/leaflet.css';

function formatPrice(price: number | null | undefined): string {
  if (price == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price);
}

function shortPrice(price: number | null | undefined): string {
  if (price == null) return '—';
  if (price >= 1_000_000) return `$${(price / 1_000_000).toFixed(price >= 10_000_000 ? 0 : 1)}M`;
  if (price >= 1_000) return `$${Math.round(price / 1_000)}K`;
  return `$${price}`;
}

/** Properties that have usable coordinates. */
function withCoords(results: Property[]): Property[] {
  return results.filter(
    (p) =>
      typeof p.lat === 'number' &&
      typeof p.lng === 'number' &&
      !Number.isNaN(p.lat) &&
      !Number.isNaN(p.lng) &&
      (p.lat !== 0 || p.lng !== 0),
  );
}

/** A rounded price-pill marker (no external icon assets needed). */
function priceIcon(price: number | null | undefined): L.DivIcon {
  return L.divIcon({
    className: 'price-marker',
    html: `<div style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;background:#ffffff;color:#0f172a;font-weight:700;font-size:12px;border-radius:9999px;box-shadow:0 1px 6px rgba(15,23,42,.28);border:1px solid #e2e8f0;white-space:nowrap;">${shortPrice(price)}</div>`,
    iconSize: [54, 26],
    iconAnchor: [27, 26],
    popupAnchor: [0, -24],
  });
}

/** Fits the viewport to all pins whenever the result set changes. */
function FitBounds({ pins }: { pins: Property[] }) {
  const map = useMap();
  useEffect(() => {
    if (pins.length === 0) return;
    if (pins.length === 1) {
      map.setView([pins[0].lat, pins[0].lng], 13);
      return;
    }
    const bounds = L.latLngBounds(pins.map((p) => [p.lat, p.lng] as [number, number]));
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 14 });
  }, [pins, map]);
  return null;
}

function NoCoords({ count }: { count: number }) {
  return (
    <div className="relative h-[28rem] overflow-hidden rounded-xl border border-dashed border-slate-300 bg-slate-50">
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 px-6 text-center text-sm text-slate-400">
        <MapPin className="h-6 w-6 text-slate-300" />
        <p className="font-medium text-slate-500">No mappable locations</p>
        <p className="text-xs">
          None of the {count} {count === 1 ? 'result' : 'results'} have coordinates to plot.
        </p>
      </div>
    </div>
  );
}

export default function LeafletMap({ results }: { results: Property[] }) {
  const pins = useMemo(() => withCoords(results), [results]);

  const center = useMemo<[number, number]>(() => {
    if (pins.length === 0) return [39.8283, -98.5795]; // Continental US
    const lat = pins.reduce((s, p) => s + p.lat, 0) / pins.length;
    const lng = pins.reduce((s, p) => s + p.lng, 0) / pins.length;
    return [lat, lng];
  }, [pins]);

  if (pins.length === 0) {
    return <NoCoords count={results.length} />;
  }

  return (
    <div className="h-[28rem] overflow-hidden rounded-xl border border-slate-200">
      <MapContainer
        center={center}
        zoom={pins.length === 1 ? 13 : 9}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds pins={pins} />
        {pins.map((p) => (
          <Marker key={p.id} position={[p.lat, p.lng]} icon={priceIcon(p.price)}>
            <Popup>
              <div className="space-y-1.5">
                <p className="text-sm font-bold text-slate-900">{formatPrice(p.price)}</p>
                <p className="flex items-start gap-1 text-xs text-slate-600">
                  <MapPin className="mt-0.5 h-3 w-3 shrink-0 text-indigo-500" />
                  <span>
                    {p.address}, {p.city} {p.state}
                  </span>
                </p>
                <p className="text-xs text-slate-500">
                  {p.beds} bd · {p.bathrooms} ba · {p.sqft.toLocaleString()} sqft
                </p>
                <Link
                  href={`/property/${p.id}`}
                  className="inline-block pt-0.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                >
                  View details →
                </Link>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
