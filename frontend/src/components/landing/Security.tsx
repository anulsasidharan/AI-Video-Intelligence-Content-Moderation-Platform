import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Shield, Lock, Eye, Database, Key, FileText, UserCheck, Globe } from 'lucide-react';

const securityFeatures = [
  {
    icon: Lock,
    title: 'JWT & API Key Auth',
    description:
      'Dual authentication — JWT tokens for web dashboard, scoped API keys for programmatic access with per-key rate limiting.',
  },
  {
    icon: UserCheck,
    title: 'Role-Based Access Control',
    description:
      'Admin and operator roles with granular endpoint permissions. Least-privilege access enforced at every layer.',
  },
  {
    icon: Eye,
    title: 'PII Detection & Masking',
    description:
      'Automatic PII detection in transcripts and metadata. Sensitive data is masked in logs and stored per GDPR retention policies.',
  },
  {
    icon: Database,
    title: 'Encrypted Storage',
    description:
      'All video artifacts stored on Google Cloud Storage (GCS) with server-side encryption. Signed URLs for secure, time-limited access.',
  },
  {
    icon: Key,
    title: 'Secrets Management',
    description:
      'Zero hardcoded credentials. All secrets via GCP Secret Manager with automatic rotation and Workload Identity Federation.',
  },
  {
    icon: FileText,
    title: 'Complete Audit Trails',
    description:
      'Every moderation decision, policy change, and API key usage is immutably logged with actor, timestamp, and context.',
  },
  {
    icon: Globe,
    title: 'GDPR-Aware Design',
    description:
      'Data export, deletion requests, and configurable retention periods built into the platform from the ground up.',
  },
  {
    icon: Shield,
    title: 'Prompt Injection Resistance',
    description:
      'AI inputs are validated and sanitized before reaching LLM agents. Tool outputs are verified to prevent adversarial manipulation.',
  },
];

const compliance = [
  { label: 'GDPR', status: 'Compliant' },
  { label: 'COPPA', status: 'Aware Design' },
  { label: 'SOC 2', status: 'In Progress' },
  { label: 'HTTPS/TLS', status: 'Enforced' },
  { label: 'HMAC Signatures', status: 'All Webhooks' },
  { label: 'Multi-Region', status: 'Cloud SQL HA' },
];

export function Security() {
  return (
    <section id="security" className="bg-slate-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">Security & Compliance</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Enterprise-grade security, built in — not bolted on
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Security is a first-class concern at every layer of VidShield AI — from input validation
            to storage encryption to audit logging.
          </p>
        </div>

        {/* Security features grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-12">
          {securityFeatures.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="bg-slate-950/60 border border-slate-800/60 rounded-2xl p-5 hover:border-slate-700 transition-colors"
              >
                <div className="w-10 h-10 bg-blue-600/10 border border-blue-500/20 rounded-xl flex items-center justify-center mb-4">
                  <Icon size={18} className="text-blue-400" />
                </div>
                <h3 className="text-white font-semibold text-sm mb-2">{feature.title}</h3>
                <p className="text-slate-500 text-xs leading-relaxed">{feature.description}</p>
              </div>
            );
          })}
        </div>

        {/* Compliance badges */}
        <div className="bg-slate-950/60 border border-slate-800/60 rounded-2xl p-6">
          <div className="text-slate-400 text-sm font-medium mb-4 text-center">
            Compliance & Trust Indicators
          </div>
          <div className="flex flex-wrap gap-3 justify-center">
            {compliance.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 bg-slate-800 border border-slate-700/60 rounded-lg px-4 py-2"
              >
                <div className="w-2 h-2 rounded-full bg-green-400" />
                <span className="text-white text-sm font-semibold">{item.label}</span>
                <span className="text-slate-400 text-xs">{item.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section CTA */}
        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors shadow-lg shadow-blue-600/20"
          >
            Start Secure — Free Trial
            <ArrowRight size={16} />
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
          >
            Contact Sales
          </Link>
        </div>
      </div>
    </section>
  );
}
