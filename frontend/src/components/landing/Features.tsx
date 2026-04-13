import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import {
  Brain,
  Video,
  Radio,
  Shield,
  BarChart3,
  Webhook,
  Bell,
  Lock,
  Layers,
  Search,
  FileText,
  Users,
} from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'Multi-Agent AI Pipeline',
    description:
      'LangGraph-orchestrated 6-agent system using GPT-4o vision for frame analysis, Whisper for audio transcription, and OCR for text extraction.',
    accent: 'blue',
  },
  {
    icon: Video,
    title: 'Video Upload & Processing',
    description:
      'Async video ingestion via S3 presigned URLs with FFmpeg/OpenCV frame extraction, thumbnail generation, and multi-format support.',
    accent: 'indigo',
  },
  {
    icon: Radio,
    title: 'Live Stream Moderation',
    description:
      'Real-time stream registration, near-real-time analysis, and WebSocket/Socket.IO alerts for instant violation detection.',
    accent: 'violet',
  },
  {
    icon: Shield,
    title: 'Policy-Driven Decisions',
    description:
      'Configurable rule sets per category — violence, nudity, drugs, hate symbols. Auto-flag, auto-reject, or escalate with full audit trail.',
    accent: 'blue',
  },
  {
    icon: BarChart3,
    title: 'Analytics & Reporting',
    description:
      'Throughput metrics, violation trends, latency percentiles, and exportable reports. Real-time dashboards with charts and heatmaps.',
    accent: 'green',
  },
  {
    icon: Webhook,
    title: 'Webhooks & REST API',
    description:
      'HMAC-signed outbound webhooks for moderation.completed, violation.detected, and stream.status events. Full REST API with rate limiting.',
    accent: 'orange',
  },
  {
    icon: Bell,
    title: 'Smart Alerts & Notifications',
    description:
      'Policy violation alerts, queue backlog monitoring, and pipeline failure notifications via email, webhook, or in-app delivery.',
    accent: 'yellow',
  },
  {
    icon: Lock,
    title: 'RBAC & Audit Logging',
    description:
      'Role-based access control with admin/operator roles. Complete audit logs for every moderation decision, policy change, and API call.',
    accent: 'red',
  },
  {
    icon: Layers,
    title: 'Multi-Tenant Architecture',
    description:
      'Tenant-isolated data, per-tenant policy configuration, and independent API key management for platform operators.',
    accent: 'purple',
  },
  {
    icon: Search,
    title: 'Similarity Search (RAG)',
    description:
      'Pinecone-powered vector similarity search for content deduplication and flagging of previously identified harmful content.',
    accent: 'teal',
  },
  {
    icon: FileText,
    title: 'Structured Moderation Reports',
    description:
      'Per-video reports with violations, timestamps, confidence scores, frame references, and recommended actions — all machine-readable.',
    accent: 'blue',
  },
  {
    icon: Users,
    title: 'Human Review Workflow',
    description:
      'Optional escalation to human review with priority queue, reviewer override actions, and full operator audit trail.',
    accent: 'slate',
  },
];

const accentMap: Record<string, string> = {
  blue: 'bg-blue-600/10 text-blue-400 border-blue-500/20',
  indigo: 'bg-indigo-600/10 text-indigo-400 border-indigo-500/20',
  violet: 'bg-violet-600/10 text-violet-400 border-violet-500/20',
  green: 'bg-green-600/10 text-green-400 border-green-500/20',
  orange: 'bg-orange-600/10 text-orange-400 border-orange-500/20',
  yellow: 'bg-yellow-600/10 text-yellow-400 border-yellow-500/20',
  red: 'bg-red-600/10 text-red-400 border-red-500/20',
  purple: 'bg-purple-600/10 text-purple-400 border-purple-500/20',
  teal: 'bg-teal-600/10 text-teal-400 border-teal-500/20',
  slate: 'bg-slate-600/10 text-slate-400 border-slate-500/20',
};

export function Features() {
  return (
    <section id="features" className="bg-slate-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">Platform Features</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Everything you need to moderate video at scale
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            A complete, production-ready platform from ingestion to report — powered by state-of-the-art AI and built for enterprise reliability.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            const accentClass = accentMap[feature.accent] ?? accentMap['blue'];
            return (
              <div
                key={feature.title}
                className="group bg-slate-900/60 border border-slate-800/60 rounded-2xl p-6 hover:border-slate-700 hover:bg-slate-900 transition-all duration-200"
              >
                <div
                  className={`w-10 h-10 rounded-xl border flex items-center justify-center mb-4 ${accentClass}`}
                >
                  <Icon size={20} />
                </div>
                <h3 className="text-white font-semibold text-base mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>

        {/* Section CTA */}
        <div className="mt-14 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors shadow-lg shadow-blue-600/20"
          >
            Start Free Trial
            <ArrowRight size={16} />
          </Link>
          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
          >
            See How It Works
          </a>
        </div>
      </div>
    </section>
  );
}
