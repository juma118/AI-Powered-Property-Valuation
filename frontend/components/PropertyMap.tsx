'use client';

import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';
import type { Property } from '@/lib/types';

// Leaflet relies on `window`, so the map is loaded client-side only (no SSR).
const LeafletMap = dynamic(() => import('./LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="flex h-[28rem] items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-400">
      <Loader2 className="h-6 w-6 animate-spin" />
    </div>
  ),
});

export default function PropertyMap({ results }: { results: Property[] }) {
  return <LeafletMap results={results} />;
}
