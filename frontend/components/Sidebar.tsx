'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import {
  LayoutDashboard,
  Search,
  MessageSquare,
  Bookmark,
  LogOut,
  Building2,
  Sparkles
} from 'lucide-react';
import { clearToken } from '@/lib/auth';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/search', label: 'Search', icon: Search },
  { href: '/chat', label: 'AI Chat', icon: MessageSquare },
  { href: '/saved', label: 'Saved', icon: Bookmark }
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.replace('/login');
  }

  function isActive(href: string) {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  }

  return (
    <>
      {/* Spacer keeps the flex column's width since the real sidebar is fixed. */}
      <div className="w-64 shrink-0" aria-hidden="true" />
      <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col overflow-hidden bg-sidebar-gradient text-slate-300 shadow-elevated">
        {/* subtle top glow */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-[radial-gradient(60%_80%_at_50%_0%,rgba(124,58,237,0.35),transparent_70%)]" />

      {/* Brand */}
      <div className="relative flex items-center gap-3 px-5 py-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
          <Building2 size={20} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-white">PropIntel</p>
          <p className="text-[11px] font-medium text-slate-400">Valuation &amp; Leads</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="relative flex-1 px-3 py-2">
        <p className="px-3 pb-2 pt-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
          Menu
        </p>
        <div className="space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  active
                    ? 'bg-white/10 text-white shadow-inner-line'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                )}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-brand-gradient" />
                )}
                <Icon
                  size={18}
                  className={clsx(
                    'transition-colors',
                    active ? 'text-brand-300' : 'text-slate-400 group-hover:text-brand-300'
                  )}
                />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Upsell card */}
      <div className="relative px-3 pb-2">
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
          <div className="mb-2 flex items-center gap-2 text-white">
            <Sparkles size={15} className="text-accent-400" />
            <span className="text-xs font-semibold">AI Insights</span>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400">
            Valuations, comps &amp; risk scores generated for every listing.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="relative border-t border-white/10 p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-400 transition-colors hover:bg-rose-500/10 hover:text-rose-300"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
      </aside>
    </>
  );
}
