'use client';

import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Sparkles, Loader2, FileText } from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';
import Sidebar from '@/components/Sidebar';
import PropertyCard from '@/components/PropertyCard';
import { chatQuery } from '@/lib/api';
import type { ChatResponse, Property } from '@/lib/types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  properties?: Property[];
  sources?: ChatResponse['sources'];
}

const EXAMPLE_PROMPTS: string[] = [
  'Find family homes near good schools under 600k',
  'Which neighborhoods have the best walk scores?',
  'Show me 3-bed properties with high investment potential',
  'What are the cheapest move-in ready homes right now?',
];

function makeId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function ChatPageInner() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: "Hi! I'm your AI property assistant. Ask me about listings, neighborhoods, valuations, or investment potential. Try one of the example prompts below to get started.",
    },
  ]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const mutation = useMutation({
    mutationFn: (query: string) => chatQuery(query),
    onSuccess: (data: ChatResponse) => {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: 'assistant',
          text: data.answer,
          properties: data.properties,
          sources: data.sources,
        },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: 'assistant',
          text: 'Sorry, something went wrong while answering that. Please try again.',
        },
      ]);
    },
  });

  // Auto-scroll to bottom on new messages / loading state changes.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, mutation.isPending]);

  function submitQuery(query: string) {
    const trimmed = query.trim();
    if (!trimmed || mutation.isPending) return;
    setMessages((prev) => [
      ...prev,
      { id: makeId(), role: 'user', text: trimmed },
    ]);
    setInput('');
    mutation.mutate(trimmed);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    submitQuery(input);
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex flex-1 flex-col">
        <header className="panel-header px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
              <Sparkles className="h-4 w-4" />
            </span>
            <h1 className="text-lg font-semibold text-slate-900">AI Property Chat</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Ask questions in plain English and get matched listings, insights, and sources.
          </p>
        </header>

        {/* Message list */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    msg.role === 'user'
                      ? 'rounded-br-sm bg-brand-gradient text-white shadow-glow'
                      : 'rounded-bl-sm bg-white text-slate-800 ring-1 ring-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {msg.properties && msg.properties.length > 0 && (
                    <div className="stagger mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                      {msg.properties.map((p) => (
                        <PropertyCard key={p.id} property={p} compact />
                      ))}
                    </div>
                  )}

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 border-t border-slate-100 pt-3">
                      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                        <FileText className="h-3.5 w-3.5" />
                        Sources
                      </div>
                      <ul className="space-y-1">
                        {msg.sources.map((s) => (
                          <li
                            key={s.property_id}
                            className="flex items-center justify-between gap-3 text-xs text-slate-500"
                          >
                            <a
                              href={`/property/${s.property_id}`}
                              className="truncate text-indigo-600 hover:underline"
                            >
                              {s.address}
                            </a>
                            <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-600">
                              {(s.score * 100).toFixed(0)}%
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {mutation.isPending && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm bg-white px-4 py-3 text-sm text-slate-500 ring-1 ring-slate-200">
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                  Thinking…
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Example prompts */}
        <div className="mx-auto w-full max-w-3xl px-4 sm:px-6">
          <div className="flex flex-wrap gap-2 pb-3">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => submitQuery(prompt)}
                disabled={mutation.isPending}
                className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input box */}
        <div className="border-t border-slate-200/70 bg-white/75 px-4 py-4 backdrop-blur-xl sm:px-6">
          <form
            onSubmit={handleSubmit}
            className="mx-auto flex w-full max-w-3xl items-end gap-2"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  submitQuery(input);
                }
              }}
              rows={1}
              placeholder="Ask about properties, neighborhoods, or valuations…"
              className="max-h-40 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={mutation.isPending || !input.trim()}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Send message"
            >
              {mutation.isPending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <AuthGuard>
      <ChatPageInner />
    </AuthGuard>
  );
}
