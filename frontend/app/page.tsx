'use client';

import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  DollarSign,
  Bookmark,
  Sparkles,
  Loader2,
  Home,
  AlertCircle,
} from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import PropertyCard from '@/components/PropertyCard';
import CountUp from '@/components/CountUp';
import { dashboardSummary, recommendations } from '@/lib/api';
import type { DashboardSummary, Property } from '@/lib/types';

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '0';
  }
  return new Intl.NumberFormat('en-US').format(value);
}

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  accent: string;
  loading?: boolean;
}

function MetricCard({ label, value, icon, accent, loading }: MetricCardProps) {
  return (
    <div className="card card-hover group p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          {loading ? (
            <div className="mt-3 h-7 w-24 animate-pulse rounded-lg bg-slate-100" />
          ) : (
            <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
              {value}
            </p>
          )}
        </div>
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-2xl ring-1 ring-inset transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-110 ${accent}`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function SectionHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
    </div>
  );
}

function PropertyGridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-72 animate-pulse rounded-2xl border border-slate-100 bg-slate-100"
        />
      ))}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
        <Home className="h-6 w-6 text-slate-400" />
      </div>
      <p className="mt-3 text-sm text-slate-500">{message}</p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <AlertCircle className="h-5 w-5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

function DashboardContent() {
  const summaryQuery = useQuery<DashboardSummary>({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardSummary,
  });

  const recommendationsQuery = useQuery<{ recommendations: Property[] }>({
    queryKey: ['dashboard', 'recommendations'],
    queryFn: recommendations,
  });

  const summary = summaryQuery.data;
  const recs = recommendationsQuery.data?.recommendations ?? [];
  const recent = summary?.recent ?? [];

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Welcome back 👋
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Your property intelligence at a glance.
        </p>
      </div>

      {/* Metric cards */}
      {summaryQuery.isError ? (
        <ErrorState message="Could not load your dashboard summary. Please try again." />
      ) : (
        <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Properties analyzed"
            value={<CountUp value={summary?.properties_analyzed ?? 0} format={formatNumber} />}
            loading={summaryQuery.isLoading}
            icon={<TrendingUp className="h-5 w-5 text-indigo-600" />}
            accent="bg-indigo-50 ring-indigo-100"
          />
          <MetricCard
            label="Average valuation"
            value={<CountUp value={summary?.avg_valuation ?? 0} format={formatCurrency} />}
            loading={summaryQuery.isLoading}
            icon={<DollarSign className="h-5 w-5 text-emerald-600" />}
            accent="bg-emerald-50 ring-emerald-100"
          />
          <MetricCard
            label="Saved properties"
            value={<CountUp value={summary?.saved_count ?? 0} format={formatNumber} />}
            loading={summaryQuery.isLoading}
            icon={<Bookmark className="h-5 w-5 text-amber-600" />}
            accent="bg-amber-50 ring-amber-100"
          />
          <MetricCard
            label="New opportunities"
            value={<CountUp value={summary?.new_opportunities ?? 0} format={formatNumber} />}
            loading={summaryQuery.isLoading}
            icon={<Sparkles className="h-5 w-5 text-fuchsia-600" />}
            accent="bg-fuchsia-50 ring-fuchsia-100"
          />
        </div>
      )}

      {/* Recommended for you */}
      <section className="mt-10">
        <SectionHeader
          title="Recommended for you"
          subtitle="AI-matched listings based on your activity."
        />
        {recommendationsQuery.isLoading ? (
          <PropertyGridSkeleton />
        ) : recommendationsQuery.isError ? (
          <ErrorState message="Could not load recommendations." />
        ) : recs.length === 0 ? (
          <EmptyState message="No recommendations yet. Analyze a few properties to get personalized matches." />
        ) : (
          <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {recs.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        )}
      </section>

      {/* Recent feed */}
      <section className="mt-10">
        <SectionHeader
          title="Recent"
          subtitle="The latest properties you've worked with."
        />
        {summaryQuery.isLoading ? (
          <PropertyGridSkeleton />
        ) : summaryQuery.isError ? (
          <ErrorState message="Could not load recent properties." />
        ) : recent.length === 0 ? (
          <EmptyState message="No recent activity. Start by searching for properties." />
        ) : (
          <div className="stagger grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {recent.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-x-hidden">
          <DashboardContent />
        </main>
      </div>
    </AuthGuard>
  );
}
