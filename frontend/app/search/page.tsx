'use client';

import { useState, FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { LayoutGrid, MapPin, Search as SearchIcon, Loader2 } from 'lucide-react';
import { searchProperties } from '@/lib/api';
import type { Property, SearchResponse } from '@/lib/types';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import PropertyCard from '@/components/PropertyCard';
import PropertyMap from '@/components/PropertyMap';

interface Filters {
  city: string;
  state: string;
  min_price: string;
  max_price: string;
  beds: string;
  baths: string;
  min_sqft: string;
  keywords: string;
}

const EMPTY_FILTERS: Filters = {
  city: '',
  state: '',
  min_price: '',
  max_price: '',
  beds: '',
  baths: '',
  min_sqft: '',
  keywords: '',
};

type ViewMode = 'list' | 'map';

function toNumber(value: string): number | undefined {
  if (value.trim() === '') return undefined;
  const n = Number(value);
  return Number.isNaN(n) ? undefined : n;
}

function buildParams(filters: Filters) {
  return {
    city: filters.city.trim() || undefined,
    state: filters.state.trim() || undefined,
    min_price: toNumber(filters.min_price),
    max_price: toNumber(filters.max_price),
    beds: toNumber(filters.beds),
    baths: toNumber(filters.baths),
    min_sqft: toNumber(filters.min_sqft),
    keywords: filters.keywords.trim() || undefined,
    limit: 20,
    offset: 0,
  };
}

function formatPrice(price: number | null | undefined): string {
  if (price == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price);
}

function MapView({ results }: { results: Property[] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="mb-4 flex items-center gap-2 text-slate-600">
        <MapPin className="h-5 w-5" />
        <span className="text-sm font-medium">
          Map view — {results.length} {results.length === 1 ? 'property' : 'properties'}
        </span>
      </div>
      <PropertyMap results={results} />
      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {results.map((p) => (
          <li
            key={p.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm"
          >
            <span className="flex min-w-0 items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0 text-indigo-500" />
              <span className="truncate text-slate-700">
                {p.address}, {p.city} {p.state}
              </span>
            </span>
            <span className="shrink-0 font-semibold text-slate-900">
              {formatPrice(p.price)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SearchPage() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [view, setView] = useState<ViewMode>('list');
  const [hasSearched, setHasSearched] = useState(false);

  const mutation = useMutation<SearchResponse, Error, Filters>({
    mutationFn: (f) => searchProperties(buildParams(f)),
  });

  const handleChange = (key: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setHasSearched(true);
    mutation.mutate(filters);
  };

  const handleReset = () => {
    setFilters(EMPTY_FILTERS);
    mutation.reset();
    setHasSearched(false);
  };

  const results = mutation.data?.results ?? [];
  const total = mutation.data?.total ?? 0;

  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-6 py-8">
            <header className="mb-6">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                Find your next <span className="gradient-text">opportunity</span>
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Search listings by location, price, size and keywords.
              </p>
            </header>

            {/* Filter bar */}
            <form
              onSubmit={handleSubmit}
              className="card mb-8 p-5"
            >
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Field label="City">
                  <input
                    type="text"
                    value={filters.city}
                    onChange={handleChange('city')}
                    placeholder="Austin"
                    className="filter-input"
                  />
                </Field>
                <Field label="State">
                  <input
                    type="text"
                    value={filters.state}
                    onChange={handleChange('state')}
                    placeholder="TX"
                    maxLength={2}
                    className="filter-input uppercase"
                  />
                </Field>
                <Field label="Min Price">
                  <input
                    type="number"
                    min={0}
                    value={filters.min_price}
                    onChange={handleChange('min_price')}
                    placeholder="0"
                    className="filter-input"
                  />
                </Field>
                <Field label="Max Price">
                  <input
                    type="number"
                    min={0}
                    value={filters.max_price}
                    onChange={handleChange('max_price')}
                    placeholder="Any"
                    className="filter-input"
                  />
                </Field>
                <Field label="Beds">
                  <input
                    type="number"
                    min={0}
                    value={filters.beds}
                    onChange={handleChange('beds')}
                    placeholder="Any"
                    className="filter-input"
                  />
                </Field>
                <Field label="Baths">
                  <input
                    type="number"
                    min={0}
                    step="0.5"
                    value={filters.baths}
                    onChange={handleChange('baths')}
                    placeholder="Any"
                    className="filter-input"
                  />
                </Field>
                <Field label="Min Sqft">
                  <input
                    type="number"
                    min={0}
                    value={filters.min_sqft}
                    onChange={handleChange('min_sqft')}
                    placeholder="Any"
                    className="filter-input"
                  />
                </Field>
                <Field label="Keywords">
                  <input
                    type="text"
                    value={filters.keywords}
                    onChange={handleChange('keywords')}
                    placeholder="pool, garage…"
                    className="filter-input"
                  />
                </Field>
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={mutation.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {mutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <SearchIcon className="h-4 w-4" />
                  )}
                  Search
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                >
                  Reset
                </button>
              </div>
            </form>

            {/* Results header + view toggle */}
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm text-slate-600">
                {mutation.isSuccess && (
                  <span>
                    <span className="font-semibold text-slate-900">{total}</span>{' '}
                    {total === 1 ? 'result' : 'results'}
                  </span>
                )}
              </div>
              <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
                <ToggleButton
                  active={view === 'list'}
                  onClick={() => setView('list')}
                  icon={<LayoutGrid className="h-4 w-4" />}
                  label="List"
                />
                <ToggleButton
                  active={view === 'map'}
                  onClick={() => setView('map')}
                  icon={<MapPin className="h-4 w-4" />}
                  label="Map"
                />
              </div>
            </div>

            {/* States */}
            {mutation.isPending && (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white py-20 text-slate-400">
                <Loader2 className="mb-3 h-8 w-8 animate-spin" />
                <p className="text-sm">Searching properties…</p>
              </div>
            )}

            {mutation.isError && (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
                Something went wrong while searching. Please try again.
              </div>
            )}

            {!mutation.isPending && !mutation.isError && hasSearched && results.length === 0 && (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-20 text-center">
                <SearchIcon className="mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm font-medium text-slate-600">No properties match your filters</p>
                <p className="mt-1 text-xs text-slate-400">Try widening your price range or removing keywords.</p>
              </div>
            )}

            {!hasSearched && !mutation.isPending && (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-20 text-center">
                <SearchIcon className="mb-3 h-8 w-8 text-slate-300" />
                <p className="text-sm font-medium text-slate-600">Start your search</p>
                <p className="mt-1 text-xs text-slate-400">Enter filters above and hit Search.</p>
              </div>
            )}

            {!mutation.isPending && !mutation.isError && results.length > 0 && (
              <>
                {view === 'list' ? (
                  <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                    {results.map((p) => (
                      <PropertyCard key={p.id} property={p} />
                    ))}
                  </div>
                ) : (
                  <MapView results={results} />
                )}
              </>
            )}
          </div>
        </main>
      </div>

      <style jsx global>{`
        .filter-input {
          width: 100%;
          border-radius: 0.5rem;
          border: 1px solid rgb(226 232 240);
          background: white;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          color: rgb(15 23 42);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }
        .filter-input:focus {
          border-color: rgb(99 102 241);
          box-shadow: 0 0 0 3px rgb(99 102 241 / 0.15);
        }
      `}</style>
    </AuthGuard>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}

function ToggleButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
        active ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
