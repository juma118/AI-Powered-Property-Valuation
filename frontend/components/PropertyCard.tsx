'use client';

import Link from 'next/link';
import { Bed, Bath, Ruler, MapPin } from 'lucide-react';
import type { Property } from '@/lib/types';

function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(price);
}

export default function PropertyCard({
  property,
  compact = false
}: {
  property: Property;
  compact?: boolean;
}) {
  const photo =
    property.photos && property.photos.length > 0
      ? property.photos[0]
      : `https://picsum.photos/seed/${property.id}/600/400`;

  return (
    <Link href={`/property/${property.id}`} className="group block">
      <article className="card card-hover overflow-hidden">
        <div
          className={`relative w-full overflow-hidden bg-gradient-to-br from-brand-100 via-slate-100 to-accent-100 ${
            compact ? 'h-32' : 'h-48'
          }`}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={photo}
            alt={property.address}
            className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-110"
          />
          {/* gradient veil for legibility */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/0 to-black/0" />

          {/* status pill */}
          <span className="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-semibold capitalize text-slate-700 shadow-sm backdrop-blur">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            {property.status}
          </span>

          {/* price pill */}
          <div className="absolute bottom-3 left-3">
            <span className="rounded-xl bg-white/95 px-3 py-1.5 text-base font-bold text-slate-900 shadow-md backdrop-blur">
              {formatPrice(property.price)}
            </span>
          </div>
        </div>

        <div className={compact ? 'p-3.5' : 'p-4'}>
          <p className="truncate text-sm font-semibold text-slate-900">
            {property.address}
          </p>
          <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
            <MapPin size={12} className="text-brand-500" />
            {property.city}, {property.state} {property.zip}
          </p>

          <div className="mt-3 flex items-center gap-2 border-t border-slate-100 pt-3 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 px-2 py-1 text-xs font-medium">
              <Bed size={14} className="text-slate-400" /> {property.beds}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 px-2 py-1 text-xs font-medium">
              <Bath size={14} className="text-slate-400" /> {property.bathrooms}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 px-2 py-1 text-xs font-medium">
              <Ruler size={14} className="text-slate-400" />{' '}
              {property.sqft.toLocaleString()}
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
