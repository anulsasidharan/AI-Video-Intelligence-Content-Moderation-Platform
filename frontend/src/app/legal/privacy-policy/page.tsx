import type { Metadata } from 'next';
import Link from 'next/link';
import { Shield, ArrowLeft } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

export const metadata: Metadata = {
  title: 'Privacy Policy — VidShield AI',
  description: 'VidShield AI Privacy Policy — how we collect, use, and protect your data.',
};

const toc = [
  { id: 'information-we-collect', label: '1. Information We Collect' },
  { id: 'how-we-use', label: '2. How We Use Your Information' },
  { id: 'data-storage', label: '3. Data Storage & Retention' },
  { id: 'sharing', label: '4. Sharing & Third-Party Services' },
  { id: 'user-rights', label: '5. Your Rights' },
  { id: 'security', label: '6. Data Security' },
  { id: 'cookies', label: '7. Cookies & Tracking' },
  { id: 'international', label: '8. International Transfers' },
  { id: 'children', label: '9. Children\'s Privacy' },
  { id: 'changes', label: '10. Changes to This Policy' },
  { id: 'contact', label: '11. Contact Us' },
];

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      <main className="pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">

          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300 text-sm mb-10 transition-colors"
          >
            <ArrowLeft size={14} />
            Back to home
          </Link>

          {/* Header */}
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
              <Shield size={14} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Legal</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">Privacy Policy</h1>
            <p className="text-slate-400 text-lg">
              Last updated: <span className="text-slate-300">[EFFECTIVE_DATE]</span>
            </p>
            <p className="text-slate-400 mt-4 leading-relaxed">
              VidShield AI (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) is committed to protecting your privacy. This
              Privacy Policy explains how we collect, use, disclose, and safeguard your information
              when you use our platform at{' '}
              <span className="text-blue-400">[WEBSITE_URL]</span>. Please read this policy carefully.
            </p>
          </div>

          {/* Table of Contents */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 mb-12">
            <h2 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">Table of Contents</h2>
            <nav>
              <ol className="space-y-2">
                {toc.map((item) => (
                  <li key={item.id}>
                    <a
                      href={`#${item.id}`}
                      className="text-slate-400 hover:text-blue-400 text-sm transition-colors"
                    >
                      {item.label}
                    </a>
                  </li>
                ))}
              </ol>
            </nav>
          </div>

          {/* Content */}
          <div className="space-y-14 text-slate-300 leading-relaxed">

            <section id="information-we-collect">
              <h2 className="text-2xl font-bold text-white mb-6">1. Information We Collect</h2>

              <h3 className="text-lg font-semibold text-white mb-3">1.1 Information You Provide Directly</h3>
              <ul className="space-y-2 mb-6 ml-4">
                {[
                  'Account registration details (name, email address, password)',
                  'Billing and payment information (processed securely via our payment provider)',
                  'Profile information and preferences',
                  'Videos, images, and media files you upload for processing',
                  'Support and communication messages',
                  'Responses to surveys or feedback forms',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>

              <h3 className="text-lg font-semibold text-white mb-3">1.2 Information Collected Automatically</h3>
              <ul className="space-y-2 mb-6 ml-4">
                {[
                  'Log data (IP address, browser type, pages visited, time and date, referring URLs)',
                  'Device information (hardware model, operating system, unique device identifiers)',
                  'Usage analytics (features used, actions taken, session duration)',
                  'Performance data (error reports, diagnostic information)',
                  'Cookies and similar tracking technologies (see Section 7)',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>

              <h3 className="text-lg font-semibold text-white mb-3">1.3 Video and Media Content</h3>
              <p className="text-slate-400">
                When you submit videos for moderation analysis, our AI pipeline processes frame data,
                audio transcriptions, and extracted metadata. This content is stored temporarily during
                analysis and retained according to your account settings and applicable data retention policies.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="how-we-use">
              <h2 className="text-2xl font-bold text-white mb-6">2. How We Use Your Information</h2>
              <p className="text-slate-400 mb-4">We use the information we collect to:</p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  { title: 'Provide the Service', desc: 'Process your videos, run AI moderation pipelines, and deliver analysis results.' },
                  { title: 'Account Management', desc: 'Create and manage your account, authenticate users, and handle billing.' },
                  { title: 'Improve & Develop', desc: 'Analyze usage patterns to improve platform features and AI model accuracy.' },
                  { title: 'Security & Fraud Prevention', desc: 'Detect and prevent unauthorized access, abuse, and policy violations.' },
                  { title: 'Communications', desc: 'Send product updates, security alerts, and respond to support requests.' },
                  { title: 'Legal Compliance', desc: 'Meet legal obligations, resolve disputes, and enforce our terms.' },
                ].map((item) => (
                  <div key={item.title} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-white font-semibold text-sm mb-1">{item.title}</div>
                    <p className="text-slate-500 text-sm">{item.desc}</p>
                  </div>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="data-storage">
              <h2 className="text-2xl font-bold text-white mb-6">3. Data Storage &amp; Retention</h2>
              <p className="text-slate-400 mb-4">
                Your data is stored on Amazon Web Services (AWS) infrastructure in the United States,
                with redundant backups and encryption at rest (AES-256).
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl overflow-hidden mb-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800/60">
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Data Type</th>
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Retention Period</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {[
                      ['Account data', 'Duration of account + 30 days after deletion request'],
                      ['Video content', 'Configurable per policy (default: 90 days)'],
                      ['Moderation reports', '12 months (enterprise: configurable)'],
                      ['Access logs', '90 days'],
                      ['Billing records', '7 years (legal requirement)'],
                      ['Support communications', '3 years'],
                    ].map(([type, period]) => (
                      <tr key={type}>
                        <td className="px-5 py-3 text-slate-300">{type}</td>
                        <td className="px-5 py-3 text-slate-400">{period}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-slate-400 text-sm">
                You may request earlier deletion at any time. See Section 5 (Your Rights) for details.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="sharing">
              <h2 className="text-2xl font-bold text-white mb-6">4. Sharing &amp; Third-Party Services</h2>
              <p className="text-slate-400 mb-6">
                We do not sell your personal data. We share information only in the following circumstances:
              </p>

              <h3 className="text-lg font-semibold text-white mb-3">4.1 Service Providers</h3>
              <p className="text-slate-400 mb-4">
                We engage trusted third parties to help operate our platform. All providers are contractually
                bound to use your data only to perform services on our behalf:
              </p>
              <ul className="space-y-2 mb-6 ml-4">
                {[
                  'AWS — cloud infrastructure and storage',
                  'OpenAI — AI model inference for video analysis',
                  'Pinecone — vector database for similarity search',
                  'Stripe — payment processing',
                  'Sentry — error monitoring',
                  'SendGrid — transactional email',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>

              <h3 className="text-lg font-semibold text-white mb-3">4.2 Legal Requirements</h3>
              <p className="text-slate-400 mb-4">
                We may disclose your information if required by law, court order, or governmental authority,
                or to protect the rights, property, or safety of VidShield AI, our users, or the public.
              </p>

              <h3 className="text-lg font-semibold text-white mb-3">4.3 Business Transfers</h3>
              <p className="text-slate-400">
                In the event of a merger, acquisition, or sale of assets, your data may be transferred
                to the acquiring entity. We will notify you before your data becomes subject to a different
                privacy policy.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="user-rights">
              <h2 className="text-2xl font-bold text-white mb-6">5. Your Rights</h2>
              <p className="text-slate-400 mb-6">
                Depending on your location, you have the following rights regarding your personal data:
              </p>
              <div className="space-y-4">
                {[
                  { right: 'Right to Access', desc: 'Request a copy of the personal data we hold about you.' },
                  { right: 'Right to Rectification', desc: 'Correct inaccurate or incomplete personal data.' },
                  { right: 'Right to Erasure', desc: 'Request deletion of your personal data ("right to be forgotten").' },
                  { right: 'Right to Data Portability', desc: 'Receive your data in a structured, machine-readable format.' },
                  { right: 'Right to Restriction', desc: 'Limit how we process your data in certain circumstances.' },
                  { right: 'Right to Object', desc: 'Object to processing based on legitimate interests or for marketing.' },
                  { right: 'Right to Withdraw Consent', desc: 'Withdraw consent at any time where processing is consent-based.' },
                ].map((item) => (
                  <div key={item.right} className="flex gap-4 p-4 bg-slate-900 border border-slate-800/60 rounded-xl">
                    <div className="w-2 h-2 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                    <div>
                      <span className="text-white font-semibold text-sm">{item.right}: </span>
                      <span className="text-slate-400 text-sm">{item.desc}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <p className="text-slate-300 text-sm">
                  To exercise any of these rights, email us at{' '}
                  <span className="text-blue-400">[CONTACT_EMAIL]</span>. We will respond within
                  30 days (GDPR: 1 month). Some rights may be limited by legal obligations.
                </p>
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="security">
              <h2 className="text-2xl font-bold text-white mb-6">6. Data Security</h2>
              <p className="text-slate-400 mb-4">
                We implement industry-standard security measures to protect your data:
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  'TLS 1.3 encryption for all data in transit',
                  'AES-256 encryption for data at rest',
                  'SOC 2 Type II certified infrastructure',
                  'Role-based access control (RBAC)',
                  'Regular penetration testing',
                  'Automated vulnerability scanning',
                  'AWS WAF and DDoS protection',
                  'Multi-factor authentication support',
                ].map((item) => (
                  <div key={item} className="flex gap-3 items-start">
                    <span className="text-green-400 mt-0.5 flex-shrink-0">✓</span>
                    <span className="text-slate-400 text-sm">{item}</span>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 mt-6 text-sm">
                Despite these measures, no transmission over the Internet is 100% secure. If you
                suspect unauthorized access to your account, contact{' '}
                <span className="text-blue-400">[CONTACT_EMAIL]</span> immediately.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="cookies">
              <h2 className="text-2xl font-bold text-white mb-6">7. Cookies &amp; Tracking</h2>
              <p className="text-slate-400 mb-4">
                We use cookies and similar technologies to operate the platform, analyze usage, and
                remember your preferences. For full details, see our{' '}
                <Link href="/legal/cookie-policy" className="text-blue-400 hover:text-blue-300 transition-colors">
                  Cookie Policy
                </Link>.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="international">
              <h2 className="text-2xl font-bold text-white mb-6">8. International Data Transfers</h2>
              <p className="text-slate-400 mb-4">
                VidShield AI is operated in the United States. If you are located outside the US,
                your data will be transferred to and processed in the US under appropriate safeguards:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'EU Standard Contractual Clauses (SCCs) for transfers from the European Economic Area',
                  'UK International Data Transfer Agreements for UK residents',
                  'Adequacy decisions where applicable',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-400 mt-4">
                For GDPR-specific rights and transfer mechanisms, see our{' '}
                <Link href="/legal/gdpr-compliance" className="text-blue-400 hover:text-blue-300 transition-colors">
                  GDPR Compliance page
                </Link>.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="children">
              <h2 className="text-2xl font-bold text-white mb-6">9. Children&apos;s Privacy</h2>
              <p className="text-slate-400">
                VidShield AI is not directed to individuals under the age of 16. We do not knowingly
                collect personal data from children. If you believe we have inadvertently collected
                such data, please contact us immediately at{' '}
                <span className="text-blue-400">[CONTACT_EMAIL]</span> and we will delete it promptly.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="changes">
              <h2 className="text-2xl font-bold text-white mb-6">10. Changes to This Policy</h2>
              <p className="text-slate-400">
                We may update this Privacy Policy from time to time. We will notify you of material
                changes by email or by posting a prominent notice on our platform at least 30 days
                before the changes take effect. Your continued use of VidShield AI after the effective
                date constitutes acceptance of the revised policy.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="contact">
              <h2 className="text-2xl font-bold text-white mb-6">11. Contact Us</h2>
              <p className="text-slate-400 mb-6">
                For privacy-related questions, data requests, or concerns, please contact:
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 space-y-3">
                <div>
                  <span className="text-slate-500 text-sm">Company</span>
                  <p className="text-white font-semibold">VidShield AI ([COMPANY_NAME])</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Address</span>
                  <p className="text-slate-300">[COMPANY_ADDRESS]</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Privacy Contact</span>
                  <p className="text-blue-400">[CONTACT_EMAIL]</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Data Protection Officer</span>
                  <p className="text-blue-400">[DPO_EMAIL]</p>
                </div>
              </div>
            </section>

          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
