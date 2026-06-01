'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bookmark, Download, Loader2, Trash2 } from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import PropertyCard from '@/components/PropertyCard';
import { listSaved, deleteSaved } from '@/lib/api';
import type { SavedProperty } from '@/lib/types';

const SAVED_QUERY_KEY = ['saved'] as const;

function escapeCsv(value: unknown): string {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function buildCsv(items: SavedProperty[]): string {
  const headers = [
    'saved_id',
    'label',
    'notes',
    'address',
    'city',
    'state',
    'zip',
    'price',
    'beds',
    'bathrooms',
    'sqft',
    'property_type',
    'status',
    'property_id',
  ];

  const rows = items.map((item) => {
    const p = item.property;
    return [
      item.id,
      item.label ?? '',
      item.notes ?? '',
      p?.address ?? '',
      p?.city ?? '',
      p?.state ?? '',
      p?.zip ?? '',
      p?.price ?? '',
      p?.beds ?? '',
      p?.bathrooms ?? '',
      p?.sqft ?? '',
      p?.property_type ?? '',
      p?.status ?? '',
      item.property_id,
    ]
      .map(escapeCsv)
      .join(',');
  });

  return [headers.join(','), ...rows].join('\r\n');
}

function downloadCsv(items: SavedProperty[]) {
  const csv = buildCsv(items);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const date = new Date().toISOString().slice(0, 10);
  link.href = url;
  link.download = `saved-properties-${date}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function SavedPageInner() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: SAVED_QUERY_KEY,
    queryFn: listSaved,
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => deleteSaved(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SAVED_QUERY_KEY });
    },
  });

  const items = data ?? [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1">
        <header className="panel-header flex flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
                <Bookmark className="h-4 w-4" />
              </span>
              <h1 className="text-lg font-semibold text-slate-900">Saved Properties</h1>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {items.length} {items.length === 1 ? 'property' : 'properties'} saved
            </p>
          </div>
          <button
            type="button"
            onClick={() => downloadCsv(items)}
            disabled={items.length === 0}
            className="btn-secondary"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </header>

        <div className="px-6 py-6">
          {isLoading && (
            <div className="flex items-center justify-center py-24 text-slate-400">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading saved properties…
            </div>
          )}

          {isError && !isLoading && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              Failed to load your saved properties. Please refresh and try again.
            </div>
          )}

          {!isLoading && !isError && items.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white py-20 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50">
                <Bookmark className="h-6 w-6 text-indigo-500" />
              </div>
              <h2 className="mt-4 text-base font-semibold text-slate-900">
                No saved properties yet
              </h2>
              <p className="mt-1 max-w-sm text-sm text-slate-500">
                Save listings from search or the AI chat to keep track of homes you are
                interested in. They will show up here.
              </p>
              <a href="/search" className="btn-primary mt-5">
                Browse properties
              </a>
            </div>
          )}

          {!isLoading && !isError && items.length > 0 && (
            <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((item) => (
                <div key={item.id} className="flex flex-col gap-3">
                  {item.property ? (
                    <PropertyCard property={item.property} />
                  ) : (
                    <div className="card p-4 text-sm text-slate-400">
                      Property details unavailable.
                    </div>
                  )}

                  <div className="card flex flex-1 flex-col gap-2 p-4">
                    {item.label && (
                      <span className="badge-brand w-fit capitalize">{item.label}</span>
                    )}
                    {item.notes ? (
                      <p className="text-sm text-slate-600">{item.notes}</p>
                    ) : (
                      <p className="text-sm italic text-slate-400">No notes</p>
                    )}

                    <button
                      type="button"
                      onClick={() => removeMutation.mutate(item.id)}
                      disabled={
                        removeMutation.isPending && removeMutation.variables === item.id
                      }
                      className="mt-2 inline-flex w-fit items-center gap-1.5 rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {removeMutation.isPending &&
                      removeMutation.variables === item.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function SavedPage() {
  return (
    <AuthGuard>
      <SavedPageInner />
    </AuthGuard>
  );
}
