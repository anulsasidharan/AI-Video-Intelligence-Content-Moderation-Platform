import Link from 'next/link';
import { Puzzle, ChevronRight, CheckCircle, Zap, Code2 } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const integrationGroups = [
  {
    category: 'Cloud Storage',
    color: 'blue',
    items: [
      { name: 'Amazon S3', desc: 'Direct S3 ingestion — point VidShield at any bucket and auto-process new uploads via S3 event notifications.' },
      { name: 'Google Cloud Storage', desc: 'Ingest from GCS buckets using service account credentials and Pub/Sub trigger notifications.' },
      { name: 'Azure Blob Storage', desc: 'Connect Blob Storage containers with Event Grid triggers for real-time video ingestion.' },
    ],
  },
  {
    category: 'Video Platforms',
    color: 'purple',
    items: [
      { name: 'Mux', desc: 'Automatically analyze every Mux asset after upload using Mux webhooks routed to VidShield.' },
      { name: 'Cloudflare Stream', desc: 'Plug VidShield into Cloudflare Stream\'s webhook system for instant post-upload analysis.' },
      { name: 'Vimeo OTT', desc: 'Moderate Vimeo OTT content with VidShield without changing your existing upload workflow.' },
    ],
  },
  {
    category: 'Notification & Alerting',
    color: 'emerald',
    items: [
      { name: 'Slack', desc: 'Push moderation alerts, escalations, and daily summaries directly to your Slack channels.' },
      { name: 'PagerDuty', desc: 'Route critical violations to PagerDuty for on-call incident management.' },
      { name: 'Microsoft Teams', desc: 'Send webhook-driven notifications to Teams channels for moderation events.' },
    ],
  },
  {
    category: 'Identity & Auth',
    color: 'amber',
    items: [
      { name: 'Auth0', desc: 'Use Auth0 as your IdP — map Auth0 roles to VidShield operator/admin roles via JWT claims.' },
      { name: 'Okta', desc: 'SAML 2.0 SSO with Okta for enterprise single sign-on and SCIM user provisioning.' },
      { name: 'Google Workspace', desc: 'OAuth 2.0 SSO via Google Workspace identity for teams that use Google.' },
    ],
  },
];

const colorMap: Record<string, string> = {
  blue: 'text-blue-400',
  purple: 'text-purple-400',
  emerald: 'text-emerald-400',
  amber: 'text-amber-400',
};

const GUIDE_STEPS = [
  { step: '1', title: 'Choose your integration', desc: 'Select the platform or service you want to connect from the list above.' },
  { step: '2', title: 'Configure credentials', desc: 'In Settings → Integrations, paste in your service credentials (API keys, service account JSON, etc.).' },
  { step: '3', title: 'Map events', desc: 'Choose which events from the external service should trigger VidShield processing.' },
  { step: '4', title: 'Test the connection', desc: 'Use the built-in test tool to fire a sample event and verify end-to-end flow.' },
  { step: '5', title: 'Monitor in real time', desc: 'Watch events flow through the dashboard and configure alerts for anomalies.' },
];

export default function IntegrationGuidePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <section className="pt-32 pb-14 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Puzzle size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Integration Guide</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4">Integrations</h1>
          <p className="text-slate-400 text-lg">
            Connect VidShield AI to your existing video infrastructure, storage, and notification stack.
            All integrations are configured from the dashboard — no code required for most setups.
          </p>
        </div>
      </section>

      <section className="pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-8">

          {/* Setup guide */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-6">
              <Zap size={15} className="text-blue-400" />
              <span className="text-white font-semibold text-lg">General setup guide</span>
            </div>
            <div className="space-y-5">
              {GUIDE_STEPS.map((s) => (
                <div key={s.step} className="flex gap-4">
                  <div className="w-8 h-8 bg-blue-600/20 border border-blue-500/30 rounded-full flex items-center justify-center text-blue-400 font-bold text-sm shrink-0">
                    {s.step}
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm mb-1">{s.title}</div>
                    <div className="text-slate-400 text-sm leading-relaxed">{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Integration groups */}
          {integrationGroups.map((group) => (
            <div key={group.category} className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-5">
                <Code2 size={15} className={colorMap[group.color]} />
                <span className="text-white font-semibold">{group.category}</span>
              </div>
              <div className="space-y-4">
                {group.items.map((item) => (
                  <div key={item.name} className="flex gap-4">
                    <CheckCircle size={15} className="text-emerald-400 mt-0.5 shrink-0" />
                    <div>
                      <div className="text-white font-medium text-sm mb-0.5">{item.name}</div>
                      <div className="text-slate-400 text-sm leading-relaxed">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Custom integration */}
          <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/20 rounded-2xl p-6">
            <h3 className="text-white font-semibold text-lg mb-2">Need a custom integration?</h3>
            <p className="text-slate-300 text-sm mb-4">
              If your platform isn&apos;t listed, you can use our REST API and webhooks to build any
              integration. Enterprise customers get dedicated integration engineering support.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link href="/docs/api-reference" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
                API Reference
              </Link>
              <Link href="/docs/webhooks" className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors">
                Webhooks Guide <ChevronRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
