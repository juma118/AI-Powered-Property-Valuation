'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * Animates a number from 0 to `value` with an ease-out curve.
 * Respects `prefers-reduced-motion` (renders the final value instantly).
 */
export default function CountUp({
  value,
  format,
  duration = 1100
}: {
  value: number;
  format?: (n: number) => string;
  duration?: number;
}) {
  const [display, setDisplay] = useState(0);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    if (reduce || !value) {
      setDisplay(value);
      return;
    }

    let start: number | null = null;
    const step = (ts: number) => {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setDisplay(value * eased);
      if (p < 1) {
        frame.current = requestAnimationFrame(step);
      } else {
        setDisplay(value);
      }
    };

    frame.current = requestAnimationFrame(step);
    return () => {
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, [value, duration]);

  const fmt = format ?? ((n: number) => n.toLocaleString());
  return <>{fmt(Math.round(display))}</>;
}
