'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bed,
  Bath,
  Ruler,
  MapPin,
  Loader2,
  Bookmark,
  Check,
  TrendingUp,
  ShieldAlert,
  Sparkles,
  GraduationCap,
  Footprints,
  Car,
  ImageIcon,
} from 'lucide-react';
import {
  getProperty,
  getComparables,
  generateAnalysis,
  addSaved,
} from '@/lib/api';
import type {
  Property,
  PropertyAnalysis,
  ComparablesResponse,
} from '@/lib/types';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import PropertyCard from '@/components/PropertyCard';

type TabKey = 'overview' | 'analytics' | 'neighborhood' | 'comparables' | 'ai';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'neighborhood', label: 'Neighborhood' },
  { key: 'comparables', label: 'Comparables' },
  { key: 'ai', label: 'AI Summary' },
];

function formatPrice(price: number | null | undefined): string {
  if (price == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price);
}

function pricePerSqft(price?: number | null, sqft?: number | null): string {
  if (!price || !sqft) return '—';
  return formatPrice(Math.round(price / sqft));
}

export default function PropertyDetailsPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : (params.id as string);
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>('overview');
  const [activePhoto, setActivePhoto] = useState(0);
  const [saved, setSaved] = useState(false);

  const propertyQuery = useQuery<Property>({
    queryKey: ['property', id],
    queryFn: () => getProperty(id),
    enabled: !!id,
  });

  const comparablesQuery = useQuery<ComparablesResponse>({
    queryKey: ['comparables', id],
    queryFn: () => getComparables(id),
    enabled: !!id && tab === 'comparables',
  });

  const analysisMutation = useMutation<PropertyAnalysis, Error, void>({
    mutationFn: () => generateAnalysis(id),
    onSuccess: (analysis) => {
      queryClient.setQueryData<Property>(['property', id], (prev) =>
        prev ? { ...prev, analysis } : prev,
      );
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => addSaved({ property_id: id }),
    onSuccess: () => setSaved(true),
  });

  if (propertyQuery.isPending) {
    return (
      <AuthGuard>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex flex-1 items-center justify-center text-slate-400">
            <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Loading property…
          </main>
        </div>
      </AuthGuard>
    );
  }

  if (propertyQuery.isError || !propertyQuery.data) {
    return (
      <AuthGuard>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex flex-1 items-center justify-center">
            <div className="rounded-2xl border border-red-200 bg-red-50 px-8 py-6 text-sm text-red-600">
              Could not load this property.
            </div>
          </main>
        </div>
      </AuthGuard>
    );
  }

  const property = propertyQuery.data;
  const analysis = property.analysis ?? analysisMutation.data ?? null;
  const neighborhood = property.neighborhood ?? null;
  const photos = property.photos ?? [];

  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-6 py-8">
            {/* Header */}
            <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{property.address}</h1>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
                  <MapPin className="h-4 w-4" />
                  {property.city}, {property.state} {property.zip}
                </p>
                <p className="mt-3 text-4xl font-extrabold tracking-tight gradient-text">
                  {formatPrice(property.price)}
                </p>
              </div>
              <button
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending || saved}
                className={
                  saved
                    ? 'btn bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200'
                    : 'btn-primary'
                }
              >
                {saveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : saved ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Bookmark className="h-4 w-4" />
                )}
                {saved ? 'Saved' : 'Save property'}
              </button>
            </div>

            {/* Quick stats */}
            <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat icon={<Bed className="h-5 w-5" />} label="Beds" value={property.beds ?? '—'} />
              <Stat icon={<Bath className="h-5 w-5" />} label="Baths" value={property.bathrooms ?? '—'} />
              <Stat
                icon={<Ruler className="h-5 w-5" />}
                label="Sqft"
                value={property.sqft ? property.sqft.toLocaleString() : '—'}
              />
              <Stat
                icon={<TrendingUp className="h-5 w-5" />}
                label="$/sqft"
                value={pricePerSqft(property.price, property.sqft)}
              />
            </div>

            {/* Tabs */}
            <div className="mb-6 flex flex-wrap gap-1 border-b border-slate-200">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`relative px-4 py-2.5 text-sm font-medium transition ${
                    tab === t.key
                      ? 'text-indigo-600'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {t.label}
                  {tab === t.key && (
                    <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-indigo-600" />
                  )}
                </button>
              ))}
            </div>

            {/* Tab panels */}
            {tab === 'overview' && (
              <section className="space-y-6">
                {/* Gallery */}
                <div className="overflow-hidden card">
                  <div className="relative aspect-[16/9] w-full bg-slate-100">
                    {photos.length > 0 ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={photos[activePhoto]}
                        alt={property.address}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-slate-300">
                        <ImageIcon className="h-10 w-10" />
                      </div>
                    )}
                  </div>
                  {photos.length > 1 && (
                    <div className="flex gap-2 overflow-x-auto p-3">
                      {photos.map((photo, i) => (
                        <button
                          key={i}
                          onClick={() => setActivePhoto(i)}
                          className={`h-16 w-24 shrink-0 overflow-hidden rounded-lg border-2 transition ${
                            i === activePhoto ? 'border-indigo-600' : 'border-transparent opacity-70 hover:opacity-100'
                          }`}
                        >
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={photo} alt={`thumb ${i + 1}`} className="h-full w-full object-cover" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="card p-6">
                  <h2 className="mb-3 text-lg font-semibold text-slate-900">Description</h2>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-slate-600">
                    {property.description || 'No description available for this listing.'}
                  </p>
                  <dl className="mt-6 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                    <Detail label="Type" value={property.property_type ?? '—'} />
                    <Detail label="Year built" value={property.year_built ?? '—'} />
                    <Detail
                      label="Lot size"
                      value={property.lot_size ? `${property.lot_size.toLocaleString()} sqft` : '—'}
                    />
                    <Detail label="Status" value={property.status ?? '—'} />
                  </dl>
                </div>
              </section>
            )}

            {tab === 'analytics' && (
              <section className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                <Card title="Price per sqft">
                  <p className="text-3xl font-bold text-slate-900">
                    {pricePerSqft(property.price, property.sqft)}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">Based on list price & sqft</p>
                </Card>
                <Card title="Estimated value">
                  <p className="text-3xl font-bold text-slate-900">
                    {formatPrice(analysis?.estimated_value)}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    {analysis ? 'AI estimated' : 'Run AI analysis for an estimate'}
                  </p>
                </Card>
                <Card title="Price evaluation">
                  <p className="text-sm leading-relaxed text-slate-600">
                    {analysis?.price_evaluation ?? 'Generate an AI analysis to see how this list price compares to estimated value.'}
                  </p>
                </Card>
              </section>
            )}

            {tab === 'neighborhood' && (
              <section className="space-y-6">
                {neighborhood ? (
                  <>
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                      <ScoreStat
                        icon={<GraduationCap className="h-5 w-5" />}
                        label="School score"
                        value={neighborhood.school_score?.toFixed(1) ?? '—'}
                      />
                      <ScoreStat
                        icon={<Footprints className="h-5 w-5" />}
                        label="Walk score"
                        value={neighborhood.walk_score ?? '—'}
                      />
                      <ScoreStat
                        icon={<Car className="h-5 w-5" />}
                        label="Commute"
                        value={neighborhood.commute_time != null ? `${neighborhood.commute_time} min` : '—'}
                      />
                      <ScoreStat
                        icon={<ShieldAlert className="h-5 w-5" />}
                        label="Crime score"
                        value={neighborhood.crime_score?.toFixed(1) ?? '—'}
                      />
                    </div>
                    <div className="card p-6">
                      <h2 className="mb-4 text-lg font-semibold text-slate-900">Nearby schools</h2>
                      {neighborhood.nearby_schools && neighborhood.nearby_schools.length > 0 ? (
                        <ul className="divide-y divide-slate-100">
                          {neighborhood.nearby_schools.map((school, i) => (
                            <li key={i} className="flex items-center gap-3 py-2.5 text-sm">
                              <GraduationCap className="h-4 w-4 text-indigo-500" />
                              <span className="text-slate-700">
                                {typeof school === 'string' ? school : JSON.stringify(school)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-slate-400">No nearby schools data.</p>
                      )}
                      {neighborhood.restaurants_count != null && (
                        <p className="mt-4 text-sm text-slate-500">
                          <span className="font-semibold text-slate-700">
                            {neighborhood.restaurants_count}
                          </span>{' '}
                          restaurants nearby
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <EmptyPanel text="No neighborhood data available for this property." />
                )}
              </section>
            )}

            {tab === 'comparables' && (
              <section className="space-y-6">
                {comparablesQuery.isPending ? (
                  <div className="flex items-center justify-center py-16 text-slate-400">
                    <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Loading comparables…
                  </div>
                ) : comparablesQuery.isError ? (
                  <EmptyPanel text="Could not load comparables." />
                ) : (
                  <>
                    {comparablesQuery.data?.stats && (
                      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                        <Stat
                          label="Avg price"
                          value={formatPrice(comparablesQuery.data.stats.avg_price)}
                        />
                        <Stat
                          label="Avg $/sqft"
                          value={formatPrice(comparablesQuery.data.stats.avg_price_per_sqft)}
                        />
                        <Stat
                          label="Subject $/sqft"
                          value={formatPrice(comparablesQuery.data.stats.subject_price_per_sqft)}
                        />
                        <Stat label="Comparables" value={comparablesQuery.data.stats.count} />
                      </div>
                    )}
                    {comparablesQuery.data && comparablesQuery.data.comparables.length > 0 ? (
                      <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                        {comparablesQuery.data.comparables.map((c) => (
                          <PropertyCard key={c.id} property={c} />
                        ))}
                      </div>
                    ) : (
                      <EmptyPanel text="No comparable properties found." />
                    )}
                  </>
                )}
              </section>
            )}

            {tab === 'ai' && (
              <section>
                {analysis ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <ScoreCard
                        icon={<TrendingUp className="h-5 w-5" />}
                        label="Investment score"
                        value={`${analysis.investment_score}/100`}
                        tone="indigo"
                      />
                      <ScoreCard
                        icon={<Sparkles className="h-5 w-5" />}
                        label="Buyer score"
                        value={`${analysis.buyer_score}/100`}
                        tone="emerald"
                      />
                      <ScoreCard
                        icon={<ShieldAlert className="h-5 w-5" />}
                        label="Risk"
                        value={analysis.risk_score?.toUpperCase() ?? '—'}
                        tone={
                          analysis.risk_score === 'high'
                            ? 'red'
                            : analysis.risk_score === 'med'
                            ? 'amber'
                            : 'emerald'
                        }
                      />
                    </div>

                    <div className="card p-6">
                      <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-900">
                        <Sparkles className="h-5 w-5 text-indigo-500" /> AI Summary
                      </h2>
                      <p className="whitespace-pre-line text-sm leading-relaxed text-slate-600">
                        {analysis.summary}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-6">
                        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-700">
                          Pros
                        </h3>
                        <ul className="space-y-2">
                          {(analysis.pros ?? []).map((pro, i) => (
                            <li key={i} className="flex gap-2 text-sm text-slate-700">
                              <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                              {pro}
                            </li>
                          ))}
                          {(!analysis.pros || analysis.pros.length === 0) && (
                            <li className="text-sm text-slate-400">None listed.</li>
                          )}
                        </ul>
                      </div>
                      <div className="rounded-2xl border border-red-200 bg-red-50/50 p-6">
                        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-red-700">
                          Cons
                        </h3>
                        <ul className="space-y-2">
                          {(analysis.cons ?? []).map((con, i) => (
                            <li key={i} className="flex gap-2 text-sm text-slate-700">
                              <span className="mt-0.5 h-4 w-4 shrink-0 text-center font-bold text-red-600">
                                ×
                              </span>
                              {con}
                            </li>
                          ))}
                          {(!analysis.cons || analysis.cons.length === 0) && (
                            <li className="text-sm text-slate-400">None listed.</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-16 text-center">
                    <Sparkles className="mb-3 h-10 w-10 text-indigo-300" />
                    <p className="text-sm font-medium text-slate-600">No AI analysis yet</p>
                    <p className="mb-5 mt-1 text-xs text-slate-400">
                      Generate an AI-powered valuation and investment breakdown.
                    </p>
                    {analysisMutation.isError && (
                      <p className="mb-3 text-xs text-red-500">
                        Failed to generate analysis. Please try again.
                      </p>
                    )}
                    <button
                      onClick={() => analysisMutation.mutate()}
                      disabled={analysisMutation.isPending}
                      className="btn-primary"
                    >
                      {analysisMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Sparkles className="h-4 w-4" />
                      )}
                      Generate analysis
                    </button>
                  </div>
                )}
              </section>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}

function Stat({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-slate-400">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="mt-1.5 text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}

function ScoreStat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="card p-5 text-center">
      <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
        {icon}
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="mt-0.5 text-xs text-slate-400">{label}</p>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-6">
      <h3 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">{title}</h3>
      {children}
    </div>
  );
}

function ScoreCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  tone: 'indigo' | 'emerald' | 'amber' | 'red';
}) {
  const tones: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
    emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    amber: 'bg-amber-50 text-amber-700 ring-amber-200',
    red: 'bg-red-50 text-red-700 ring-red-200',
  };
  return (
    <div className={`rounded-2xl p-6 ring-1 ${tones[tone]}`}>
      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
        {icon}
        {label}
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 font-medium text-slate-800">{value}</dd>
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-16 text-center text-sm text-slate-400">
      {text}
    </div>
  );
}
