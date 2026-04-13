import Link from 'next/link';
import { Code2, Key, Webhook, Package, Puzzle, BookOpen, Zap, ArrowRight } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const devResources = [
  {
    icon: Code2,
    title: 'API Reference',
    desc: 'Complete REST API documentation with request/response examples for every endpoint.',
    href: '/docs/api-reference',
    color: 'blue',
  },
  {
    icon: Webhook,
    title: 'Webhooks Guide',
    desc: 'Set up real-time event notifications. Learn to verify signatures and handle retries.',
    href: '/docs/webhooks',
    color: 'purple',
  },
  {
    icon: Package,
    title: 'SDK Documentation',
    desc: 'Official Python, Node.js, and Go client libraries with installation guides and examples.',
    href: '/docs/sdk',
    color: 'emerald',
  },
  {
    icon: Puzzle,
    title: 'Integration Guide',
    desc: 'Connect VidShield to S3, Mux, Slack, Auth0, and 20+ other platforms.',
    href: '/docs/integrations',
    color: 'amber',
  },
];

const quickstarts = [
  {
    title: 'Upload your first video',
    steps: [
      'Create an account and generate an API key',
      'POST to /api/v1/videos with your video file or URL',
      'Poll GET /api/v1/videos/{id} until status is "completed"',
      'Read moderation_status and violations from the response',
    ],
  },
  {
    title: 'Set up real-time webhooks',
    steps: [
      'Create an HTTPS endpoint on your server',
      'Register it in Settings → Webhooks → Add Endpoint',
      'Subscribe to video.processed and moderation.decision',
      'Verify X-VidShield-Signature on each incoming request',
    ],
  },
  {
    title: 'Generate a PDF report',
    steps: [
      'POST to /api/v1/reports/preview to confirm data scope',
      'POST to /api/v1/reports/generate to enqueue async generation',
      'Poll GET /api/v1/reports/{id} until status is "ready"',
      'GET /api/v1/reports/{id}/download for a presigned S3 URL',
    ],
  },
];

const colorMap: Record<string, string> = {
  blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
  purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
  emerald: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
};

export default function DeveloperPortalPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <BookOpen size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Developer Portal</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Developer Portal</h1>
          <p className="text-slate-400 text-lg">
            Everything you need to build on top of VidShield AI — API docs, SDKs, webhooks,
            integration guides, and working quickstart examples.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              <Key size={16} />
              Get your API key
            </Link>
            <Link
              href="/docs/api-reference"
              className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Browse API docs <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* Resources */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-center">Developer resources</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {devResources.map((r) => (
              <Link
                key={r.title}
                href={r.href}
                className="group bg-slate-900 border border-slate-800/60 rounded-2xl p-6 hover:border-slate-700/60 transition-colors"
              >
                <div className={`w-10 h-10 border rounded-xl flex items-center justify-center mb-4 ${colorMap[r.color]}`}>
                  <r.icon size={18} />
                </div>
                <div className="text-white font-semibold text-lg mb-2 group-hover:text-blue-400 transition-colors">
                  {r.title}
                </div>
                <p className="text-slate-400 text-sm leading-relaxed">{r.desc}</p>
                <div className="flex items-center gap-1 mt-4 text-blue-400 text-sm">
                  Read docs <ArrowRight size={14} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Quickstarts */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8 bg-slate-900/30">
        <div className="max-w-5xl mx-auto py-14">
          <div className="text-center mb-10">
            <div className="flex items-center justify-center gap-2 mb-3">
              <Zap size={16} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-semibold uppercase tracking-wider">Quickstarts</span>
            </div>
            <h2 className="text-2xl font-bold">Common workflows</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {quickstarts.map((qs) => (
              <div key={qs.title} className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5">
                <h3 className="text-white font-semibold mb-4 text-sm">{qs.title}</h3>
                <ol className="space-y-2">
                  {qs.steps.map((step, i) => (
                    <li key={i} className="flex gap-2 text-sm">
                      <span className="text-blue-400 font-bold shrink-0">{i + 1}.</span>
                      <span className="text-slate-400">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Base URL + key info */}
      <section className="pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4">API base URL</h3>
            <div className="bg-slate-800 border border-slate-700/60 rounded-xl px-4 py-3 mb-3">
              <code className="text-emerald-400 text-sm">https://www.orionvexa.ca/api/v1</code>
            </div>
            <p className="text-slate-500 text-sm">
              All endpoints are versioned under <code className="text-slate-400">/api/v1</code>.
              We notify you of breaking changes 90 days in advance.
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4">Rate limits</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Free plan</span>
                <span className="text-white font-medium">100 req / min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Business plan</span>
                <span className="text-white font-medium">1,000 req / min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Enterprise</span>
                <span className="text-white font-medium">Custom</span>
              </div>
            </div>
            <p className="text-slate-500 text-sm mt-3">
              Rate limit headers are included in every response:
              <code className="text-slate-400 block mt-1">X-RateLimit-Remaining</code>
              <code className="text-slate-400">X-RateLimit-Reset</code>
            </p>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
