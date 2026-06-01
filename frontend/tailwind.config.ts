import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        // Brand = indigo, used across buttons, links, sidebar and accents.
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b'
        },
        // Accent = violet, for gradients and highlights.
        accent: {
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9'
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif'
        ]
      },
      boxShadow: {
        // Soft, layered elevation for a premium feel.
        card: '0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)',
        'card-hover':
          '0 10px 30px -10px rgba(79,70,229,0.18), 0 8px 16px -8px rgba(16,24,40,0.12)',
        elevated:
          '0 20px 45px -20px rgba(16,24,40,0.30), 0 10px 20px -12px rgba(16,24,40,0.18)',
        glow: '0 0 0 1px rgba(99,102,241,0.10), 0 12px 30px -8px rgba(79,70,229,0.45)',
        'inner-line': 'inset 0 0 0 1px rgba(255,255,255,0.06)'
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        'brand-gradient-soft':
          'linear-gradient(135deg, rgba(79,70,229,0.12) 0%, rgba(124,58,237,0.12) 100%)',
        'sidebar-gradient':
          'linear-gradient(180deg, #1e1b4b 0%, #0f172a 55%, #020617 100%)'
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' }
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' }
        }
      },
      animation: {
        'fade-up': 'fade-up 0.45s cubic-bezier(0.16,1,0.3,1) both',
        float: 'float 7s ease-in-out infinite'
      }
    }
  },
  plugins: []
};

export default config;
