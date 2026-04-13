import Link from 'next/link';
import { Code2, Key, Lock, Zap, Copy, ChevronRight } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const BASE_URL = 'https://www.orionvexa.ca/api/v1';

const endpoints = [
  {
    group: 'Authentication',
    color: 'blue',
    items: [
      { method: 'POST', path: '/auth/login', desc: 'Obtain an access token and refresh token' },
      { method: 'POST', path: '/auth/refresh', desc: 'Exchange a refresh token for a new access token' },
      { method: 'POST', path: '/auth/logout', desc: 'Revoke the current session' },
    ],
  },
  {
    group: 'Videos',
    color: 'purple',
    items: [
      { method: 'GET', path: '/videos', desc: 'List videos with pagination and filters' },
      { method: 'POST', path: '/videos', desc: 'Upload and enqueue a new video for processing' },
      { method: 'GET', path: '/videos/{id}', desc: 'Retrieve a single video and its analysis results' },
      { method: 'DELETE', path: '/videos/{id}', desc: 'Soft-delete a video and its associated data' },
    ],
  },
  {
    group: 'Moderation',
    color: 'amber',
    items: [
      { method: 'GET', path: '/moderation/queue', desc: 'List moderation queue items' },
      { method: 'PATCH', path: '/moderation/{id}', desc: 'Update the moderation decision for an item' },
      { method: 'GET', path: '/moderation/policies', desc: 'List active content policies' },
      { method: 'POST', path: '/moderation/policies', desc: 'Create or update a content policy' },
    ],
  },
  {
    group: 'Analytics',
    color: 'emerald',
    items: [
      { method: 'GET', path: '/analytics/summary', desc: 'Aggregated moderation metrics for a date range' },
      { method: 'GET', path: '/analytics/violations', desc: 'Time-series and breakdown of violations' },
    ],
  },
  {
    group: 'Reports',
    color: 'pink',
    items: [
      { method: 'POST', path: '/reports/preview', desc: 'Preview report data before generating PDF' },
      { method: 'POST', path: '/reports/generate', desc: 'Enqueue async PDF report generation' },
      { method: 'GET', path: '/reports/{id}/download', desc: 'Get a presigned S3 URL to download the PDF' },
    ],
  },
];

const methodColors: Record<string, string> = {
  GET: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  POST: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  PATCH: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  DELETE: 'bg-red-500/15 text-red-400 border-red-500/20',
};

const groupColors: Record<string, string> = {
  blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
  purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  pink: 'bg-pink-500/10 border-pink-500/20 text-pink-400',
};

export default function ApiReferencePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Code2 size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">API Reference</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">REST API Reference</h1>
          <p className="text-slate-400 text-lg">
            The VidShield AI API is organized around REST. All requests accept and return
            JSON. Authentication uses Bearer tokens obtained from the{' '}
            <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded text-sm">/auth/login</code> endpoint.
          </p>
        </div>
      </section>

      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* Base URL */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={15} className="text-blue-400" />
              <span className="text-white font-semibold">Base URL</span>
            </div>
            <div className="flex items-center gap-3 bg-slate-800 border border-slate-700/60 rounded-xl px-4 py-3">
              <code className="text-emerald-400 text-sm flex-1">{BASE_URL}</code>
              <Copy size={14} className="text-slate-500 cursor-pointer hover:text-slate-300 shrink-0" />
            </div>
          </div>

          {/* Auth */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Key size={15} className="text-amber-400" />
              <span className="text-white font-semibold">Authentication</span>
            </div>
            <p className="text-slate-400 text-sm mb-4">
              Include your access token in the{' '}
              <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">Authorization</code> header
              of every request:
            </p>
            <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4">
              <pre className="text-sm text-slate-300 overflow-x-auto">
{`Authorization: Bearer <your_access_token>
Content-Type: application/json`}
              </pre>
            </div>
          </div>

          {/* Response envelope */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lock size={15} className="text-purple-400" />
              <span className="text-white font-semibold">Response format</span>
            </div>
            <p className="text-slate-400 text-sm mb-4">
              All successful responses are wrapped in a{' '}
              <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">data</code>{' '}
              envelope. Errors return an{' '}
              <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">error</code> object
              with <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">code</code> and{' '}
              <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded">message</code> fields.
            </p>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4">
                <div className="text-emerald-400 text-xs font-semibold mb-2">Success (200)</div>
                <pre className="text-xs text-slate-300 overflow-x-auto">{`{
  "data": { ... }
}`}</pre>
              </div>
              <div className="bg-slate-800 border border-slate-700/60 rounded-xl p-4">
                <div className="text-red-400 text-xs font-semibold mb-2">Error (4xx / 5xx)</div>
                <pre className="text-xs text-slate-300 overflow-x-auto">{`{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "..."
  }
}`}</pre>
              </div>
            </div>
          </div>

          {/* Endpoints */}
          {endpoints.map((group) => (
            <div key={group.group} className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold mb-4 ${groupColors[group.color]}`}>
                {group.group}
              </div>
              <div className="space-y-3">
                {group.items.map((item) => (
                  <div
                    key={item.path}
                    className="flex items-center gap-3 bg-slate-800/50 rounded-xl px-4 py-3"
                  >
                    <span className={`text-xs font-bold px-2 py-0.5 rounded border shrink-0 ${methodColors[item.method]}`}>
                      {item.method}
                    </span>
                    <code className="text-slate-300 text-sm shrink-0">{item.path}</code>
                    <span className="text-slate-500 text-sm hidden sm:block">—</span>
                    <span className="text-slate-500 text-sm hidden sm:block">{item.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* CTA */}
          <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/20 rounded-2xl p-6 text-center">
            <p className="text-slate-300 mb-4">
              Need an API key to get started? Create a free account and generate one in the dashboard.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/register" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
                Get API key
              </Link>
              <Link href="/docs/developer-portal" className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
                Developer Portal <ChevronRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
