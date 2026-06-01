'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import {
  Loader2,
  Lock,
  Mail,
  User,
  Building2,
  Sparkles,
  LineChart,
  MessageSquare,
  ShieldCheck
} from 'lucide-react';
import { login, register } from '@/lib/api';
import { setToken } from '@/lib/auth';
import type { Token } from '@/lib/types';

type Mode = 'login' | 'register';

const DEMO_EMAIL = 'demo@proptech.io';
const DEMO_PASSWORD = 'demo1234';

const FEATURES = [
  {
    icon: LineChart,
    title: 'AI valuations & scores',
    desc: 'Investment, buyer and risk scores for every listing.'
  },
  {
    icon: Sparkles,
    title: 'Comps & enrichment',
    desc: 'Neighborhoods, schools and comparable sales, automatically.'
  },
  {
    icon: MessageSquare,
    title: 'Ask in plain English',
    desc: '“Family homes near good schools under 600k.”'
  }
];

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSuccess = (data: Token) => {
    setToken(data.access_token);
    router.push('/');
  };

  const extractError = (err: unknown): string => {
    const anyErr = err as {
      response?: { data?: { detail?: unknown } };
      message?: string;
    };
    const detail = anyErr?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (anyErr?.message) return anyErr.message;
    return 'Something went wrong. Please try again.';
  };

  const loginMutation = useMutation({
    mutationFn: () => login({ email, password }),
    onSuccess: handleSuccess,
    onError: (err) => setError(extractError(err))
  });

  const registerMutation = useMutation({
    mutationFn: () => register({ email, password, full_name: fullName }),
    onSuccess: handleSuccess,
    onError: (err) => setError(extractError(err))
  });

  const isLoading = loginMutation.isPending || registerMutation.isPending;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (mode === 'login') loginMutation.mutate();
    else registerMutation.mutate();
  };

  const onGoogle = () => {
    setError(null);
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    loginMutation.mutate();
  };

  const fillDemo = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(null);
  };

  return (
    <div className="min-h-screen w-full lg:grid lg:grid-cols-[1.05fr_1fr]">
      {/* ============================= LEFT: brand hero ===================== */}
      <aside className="animated-gradient relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-accent-600 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        {/* decorative layers */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-white/15 blur-3xl animate-float" />
          <div className="absolute -bottom-24 right-0 h-96 w-96 rounded-full bg-accent-400/30 blur-3xl animate-float [animation-delay:2s]" />
          <div
            className="absolute inset-0 opacity-[0.12]"
            style={{
              backgroundImage:
                'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
              backgroundSize: '22px 22px'
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-brand-900/40 to-transparent" />
        </div>

        {/* brand */}
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/25 backdrop-blur">
            <Building2 className="h-6 w-6 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">PropIntel</span>
        </div>

        {/* headline + features */}
        <div className="relative max-w-md">
          <h2 className="animate-fade-up text-4xl font-bold leading-tight tracking-tight">
            Property intelligence,
            <br />
            powered by AI.
          </h2>
          <p className="mt-4 animate-fade-up text-sm leading-relaxed text-white/70 [animation-delay:120ms]">
            Value any home, surface the best opportunities, and get an instant
            investment breakdown — all in one workspace.
          </p>

          <ul className="stagger mt-10 space-y-5">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <li
                key={title}
                className="group flex items-start gap-4 transition-transform duration-300 hover:translate-x-1"
              >
                <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/20 backdrop-blur transition-all duration-300 group-hover:scale-110 group-hover:bg-white/25 group-hover:ring-white/40">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold">{title}</p>
                  <p className="text-sm text-white/65">{desc}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* footer stats */}
        <div className="relative flex animate-fade-up items-center gap-8 text-sm [animation-delay:320ms]">
          <Stat value="30K+" label="Listings analyzed" />
          <div className="h-8 w-px bg-white/20" />
          <Stat value="8" label="Markets" />
          <div className="h-8 w-px bg-white/20" />
          <Stat value="<2s" label="To insights" />
        </div>
      </aside>

      {/* ============================= RIGHT: form ========================= */}
      <div className="flex min-h-screen items-center justify-center bg-white px-6 py-12">
        <div className="stagger w-full max-w-sm">
          {/* mobile brand */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-glow">
              <Building2 className="h-6 w-6" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-slate-900">
              PropIntel
            </span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p className="mt-1.5 text-sm text-slate-500">
            {mode === 'login'
              ? 'Sign in to your property intelligence workspace.'
              : 'Start valuing properties in seconds.'}
          </p>

          {/* toggle */}
          <div className="mt-7 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className={`rounded-lg py-2 text-sm font-medium transition-colors ${
                mode === 'login'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => switchMode('register')}
              className={`rounded-lg py-2 text-sm font-medium transition-colors ${
                mode === 'register'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Create account
            </button>
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            {mode === 'register' && (
              <Field label="Full name" htmlFor="fullName" icon={<User className="h-4 w-4" />}>
                <input
                  id="fullName"
                  type="text"
                  autoComplete="name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  placeholder="Jane Agent"
                  className="auth-input"
                />
              </Field>
            )}

            <Field label="Email" htmlFor="email" icon={<Mail className="h-4 w-4" />}>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@company.com"
                className="auth-input"
              />
            </Field>

            <Field
              label="Password"
              htmlFor="password"
              icon={<Lock className="h-4 w-4" />}
              action={
                mode === 'login' ? (
                  <button
                    type="button"
                    onClick={() =>
                      setError('Password reset is not available in this demo.')
                    }
                    className="text-xs font-medium text-brand-600 hover:text-brand-700"
                  >
                    Forgot password?
                  </button>
                ) : undefined
              }
            >
              <input
                id="password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                placeholder="••••••••"
                className="auth-input"
              />
            </Field>

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">
                {error}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="btn-primary w-full">
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <div className="my-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-slate-200" />
            <span className="text-xs uppercase tracking-wide text-slate-400">or</span>
            <div className="h-px flex-1 bg-slate-200" />
          </div>

          <button
            type="button"
            onClick={onGoogle}
            disabled={isLoading}
            className="btn-secondary w-full"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <button
            type="button"
            onClick={fillDemo}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-3 py-2.5 text-xs text-slate-500 transition hover:border-brand-300 hover:bg-brand-50/50"
          >
            <ShieldCheck className="h-3.5 w-3.5 text-brand-500" />
            Use demo account:{' '}
            <span className="font-semibold text-slate-700">{DEMO_EMAIL}</span>
            <span className="text-slate-300">/</span>
            <span className="font-semibold text-slate-700">{DEMO_PASSWORD}</span>
          </button>

          <p className="mt-6 text-center text-xs text-slate-400">
            By continuing you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-white/60">{label}</p>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  icon,
  action,
  children
}: {
  label: string;
  htmlFor: string;
  icon: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <label htmlFor={htmlFor} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
        {action}
      </div>
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
          {icon}
        </span>
        {children}
      </div>
      <style jsx global>{`
        .auth-input {
          width: 100%;
          border-radius: 0.75rem;
          border: 1px solid rgb(226 232 240);
          background: rgb(248 250 252);
          padding: 0.625rem 0.875rem 0.625rem 2.5rem;
          font-size: 0.875rem;
          color: rgb(15 23 42);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
        }
        .auth-input::placeholder {
          color: rgb(148 163 184);
        }
        .auth-input:focus {
          border-color: rgb(99 102 241);
          background: white;
          box-shadow: 0 0 0 4px rgb(99 102 241 / 0.15);
        }
      `}</style>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#FFC107"
        d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"
      />
      <path
        fill="#FF3D00"
        d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"
      />
    </svg>
  );
}
