import type { Metadata } from 'next';
import Link from 'next/link';
import { Shield, ArrowLeft, FileText } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

export const metadata: Metadata = {
  title: 'Terms & Conditions — VidShield AI',
  description: 'VidShield AI Terms & Conditions — rules governing your use of our platform.',
};

const toc = [
  { id: 'acceptance', label: '1. Acceptance of Terms' },
  { id: 'description', label: '2. Description of Service' },
  { id: 'accounts', label: '3. User Accounts' },
  { id: 'usage-rules', label: '4. Acceptable Use Policy' },
  { id: 'prohibited', label: '5. Prohibited Activities' },
  { id: 'ip', label: '6. Intellectual Property' },
  { id: 'content', label: '7. User Content' },
  { id: 'payment', label: '8. Payment & Subscriptions' },
  { id: 'disclaimers', label: '9. Disclaimers' },
  { id: 'liability', label: '10. Limitation of Liability' },
  { id: 'indemnification', label: '11. Indemnification' },
  { id: 'termination', label: '12. Termination' },
  { id: 'disputes', label: '13. Dispute Resolution' },
  { id: 'governing-law', label: '14. Governing Law' },
  { id: 'modifications', label: '15. Modifications to Terms' },
  { id: 'contact', label: '16. Contact Information' },
];

export default function TermsConditionsPage() {
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
              <FileText size={14} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Legal</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">Terms &amp; Conditions</h1>
            <p className="text-slate-400 text-lg">
              Last updated: <span className="text-slate-300">[EFFECTIVE_DATE]</span>
            </p>
            <p className="text-slate-400 mt-4 leading-relaxed">
              These Terms &amp; Conditions (&quot;Terms&quot;) govern your access to and use of VidShield AI
              (&quot;[COMPANY_NAME]&quot;, &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) at{' '}
              <span className="text-blue-400">[WEBSITE_URL]</span>. By accessing or using our platform,
              you agree to be bound by these Terms. If you do not agree, do not use our service.
            </p>
          </div>

          {/* Important notice */}
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-10">
            <p className="text-amber-300 text-sm font-semibold mb-1">Important Notice</p>
            <p className="text-amber-200/70 text-sm">
              Please read these Terms carefully before using VidShield AI. They contain important
              information about your legal rights and obligations, including limitations on liability
              and dispute resolution provisions.
            </p>
          </div>

          {/* Table of Contents */}
          <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 mb-12">
            <h2 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">Table of Contents</h2>
            <nav>
              <ol className="grid sm:grid-cols-2 gap-2">
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

            <section id="acceptance">
              <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-slate-400 mb-4">
                By creating an account, accessing, or using VidShield AI, you confirm that:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'You are at least 18 years of age or have parental/guardian consent',
                  'You have the legal authority to enter into a binding contract',
                  'You have read and agree to these Terms and our Privacy Policy',
                  'If acting on behalf of an organization, you have authority to bind that organization',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="description">
              <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
              <p className="text-slate-400 mb-4">
                VidShield AI provides an enterprise-grade AI Video Intelligence &amp; Content Moderation
                Platform (&quot;Service&quot;) including:
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  { title: 'AI Video Moderation', desc: 'Automated content safety analysis for uploaded and live-streamed videos.' },
                  { title: 'Multi-Agent Pipeline', desc: 'LangGraph-powered agents for scene classification, object detection, and OCR.' },
                  { title: 'Policy Management', desc: 'Configurable content policies, moderation rules, and automated decision-making.' },
                  { title: 'Analytics & Reporting', desc: 'Dashboards, audit logs, and exportable reports on moderation activity.' },
                  { title: 'API Access', desc: 'RESTful API and webhooks for integrating moderation into your own workflows.' },
                  { title: 'Live Stream Analysis', desc: 'Real-time moderation for live video streams with instant alert capabilities.' },
                ].map((item) => (
                  <div key={item.title} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-white font-semibold text-sm mb-1">{item.title}</div>
                    <p className="text-slate-500 text-sm">{item.desc}</p>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 mt-6">
                We reserve the right to modify, suspend, or discontinue any part of the Service at any
                time with reasonable notice.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="accounts">
              <h2 className="text-2xl font-bold text-white mb-4">3. User Accounts</h2>
              <p className="text-slate-400 mb-4">
                To access most features, you must create an account. You agree to:
              </p>
              <ul className="space-y-2 ml-4 mb-4">
                {[
                  'Provide accurate, current, and complete registration information',
                  'Maintain the security of your password and notify us immediately of unauthorized access',
                  'Not share your account credentials with any third party',
                  'Accept responsibility for all activities that occur under your account',
                  'Keep your contact information current so we can reach you',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-400">
                We reserve the right to suspend or terminate accounts that violate these Terms or
                engage in fraudulent activity.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="usage-rules">
              <h2 className="text-2xl font-bold text-white mb-4">4. Acceptable Use Policy</h2>
              <p className="text-slate-400 mb-4">You agree to use VidShield AI only for lawful purposes, including:</p>
              <ul className="space-y-2 ml-4">
                {[
                  'Moderating content on platforms you own or have explicit authorization to moderate',
                  'Processing videos in compliance with applicable laws and regulations',
                  'Respecting privacy rights of individuals depicted in processed content',
                  'Complying with applicable data protection laws (GDPR, CCPA, etc.)',
                  'Using API access within documented rate limits and quotas',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-green-400 mt-1 flex-shrink-0">✓</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="prohibited">
              <h2 className="text-2xl font-bold text-white mb-4">5. Prohibited Activities</h2>
              <p className="text-slate-400 mb-4">
                You must not use VidShield AI to:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'Upload or process content that is illegal under applicable law',
                  'Attempt to reverse-engineer, decompile, or extract our AI models',
                  'Circumvent rate limits, abuse the API, or perform load testing without authorization',
                  'Use the platform to train competing AI models without written consent',
                  'Transmit malware, viruses, or other malicious code',
                  'Violate the privacy or intellectual property rights of others',
                  'Impersonate any person or entity or misrepresent your affiliation',
                  'Engage in any activity that disrupts or interferes with our infrastructure',
                  'Resell or sublicense access to the platform without authorization',
                  'Use automated means to scrape data beyond what the API permits',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-red-400 mt-1 flex-shrink-0">✗</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="ip">
              <h2 className="text-2xl font-bold text-white mb-4">6. Intellectual Property</h2>
              <h3 className="text-lg font-semibold text-white mb-3">6.1 VidShield AI IP</h3>
              <p className="text-slate-400 mb-6">
                The VidShield AI platform, including its software, AI models, algorithms, design, and
                documentation, is owned by [COMPANY_NAME] and protected by intellectual property laws.
                We grant you a limited, non-exclusive, non-transferable license to use the Service
                during your subscription term.
              </p>
              <h3 className="text-lg font-semibold text-white mb-3">6.2 Your IP</h3>
              <p className="text-slate-400">
                You retain all intellectual property rights in the content you upload. By submitting
                content to VidShield AI, you grant us a limited license to process that content solely
                for the purpose of providing the Service to you.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="content">
              <h2 className="text-2xl font-bold text-white mb-4">7. User Content</h2>
              <p className="text-slate-400 mb-4">
                You are solely responsible for the content you submit. You represent and warrant that:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'You have all necessary rights and permissions to submit the content',
                  'The content does not violate any law or third-party rights',
                  'You have obtained all required consents from individuals appearing in videos',
                  'The content complies with applicable data protection and privacy laws',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-400 mt-4">
                We reserve the right to remove content that violates these Terms without notice.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="payment">
              <h2 className="text-2xl font-bold text-white mb-4">8. Payment &amp; Subscriptions</h2>
              <p className="text-slate-400 mb-4">
                Paid plans are billed in advance on a monthly or annual basis. By subscribing, you authorize
                us to charge your payment method on a recurring basis.
              </p>
              <ul className="space-y-2 ml-4 mb-4">
                {[
                  'Prices are listed in USD and exclude applicable taxes',
                  'Annual subscriptions receive a discount over monthly billing',
                  'Failed payments may result in service suspension after a grace period',
                  'Unused credits do not roll over between billing periods',
                  'Refunds are issued at our discretion; contact support within 14 days of billing',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-400">
                You may cancel your subscription at any time from your account settings. Cancellation
                takes effect at the end of the current billing period.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="disclaimers">
              <h2 className="text-2xl font-bold text-white mb-4">9. Disclaimers</h2>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl p-5">
                <p className="text-slate-400 text-sm mb-3">
                  THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF
                  ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
                </p>
                <ul className="space-y-2 ml-4 text-sm">
                  {[
                    'Warranties of merchantability or fitness for a particular purpose',
                    'Guarantees of uninterrupted, error-free, or secure service',
                    'Accuracy or completeness of AI moderation decisions',
                    'Results obtained from use of the service',
                  ].map((item) => (
                    <li key={item} className="flex gap-3">
                      <span className="text-amber-400 mt-1 flex-shrink-0">•</span>
                      <span className="text-slate-400">{item}</span>
                    </li>
                  ))}
                </ul>
                <p className="text-slate-400 text-sm mt-3">
                  AI moderation decisions are probabilistic and should not be relied upon as the sole
                  determination of content legality or appropriateness.
                </p>
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="liability">
              <h2 className="text-2xl font-bold text-white mb-4">10. Limitation of Liability</h2>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl p-5">
                <p className="text-slate-400 text-sm mb-3">
                  TO THE MAXIMUM EXTENT PERMITTED BY LAW, [COMPANY_NAME] SHALL NOT BE LIABLE FOR:
                </p>
                <ul className="space-y-2 ml-4 text-sm">
                  {[
                    'Indirect, incidental, special, consequential, or punitive damages',
                    'Loss of profits, revenue, data, or business opportunities',
                    'Damages arising from unauthorized access to or alteration of your data',
                    'Any matter beyond our reasonable control',
                  ].map((item) => (
                    <li key={item} className="flex gap-3">
                      <span className="text-amber-400 mt-1 flex-shrink-0">•</span>
                      <span className="text-slate-400">{item}</span>
                    </li>
                  ))}
                </ul>
                <p className="text-slate-400 text-sm mt-3">
                  Our total aggregate liability to you shall not exceed the greater of (a) the amounts
                  paid by you in the twelve (12) months preceding the claim, or (b) one hundred US
                  dollars ($100).
                </p>
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="indemnification">
              <h2 className="text-2xl font-bold text-white mb-4">11. Indemnification</h2>
              <p className="text-slate-400">
                You agree to indemnify, defend, and hold harmless [COMPANY_NAME] and its officers,
                directors, employees, and agents from any claims, liabilities, damages, losses, and
                expenses (including reasonable attorney&apos;s fees) arising from your use of the Service,
                your User Content, your violation of these Terms, or your violation of any third-party rights.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="termination">
              <h2 className="text-2xl font-bold text-white mb-4">12. Termination</h2>
              <p className="text-slate-400 mb-4">
                Either party may terminate this agreement at any time:
              </p>
              <ul className="space-y-2 ml-4 mb-4">
                {[
                  'You may cancel your account at any time via account settings',
                  'We may suspend or terminate your access for violations of these Terms',
                  'We may terminate the Service with 30 days\' written notice for any reason',
                  'We may terminate immediately for serious violations (fraud, illegal activity)',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
              <p className="text-slate-400">
                Upon termination, your right to use the Service ceases immediately. We will retain
                your data for 30 days post-termination during which you may request an export.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="disputes">
              <h2 className="text-2xl font-bold text-white mb-4">13. Dispute Resolution</h2>
              <p className="text-slate-400 mb-4">
                Before initiating formal proceedings, you agree to contact us at{' '}
                <span className="text-blue-400">[CONTACT_EMAIL]</span> to attempt to resolve
                disputes informally. We will respond within 30 days.
              </p>
              <p className="text-slate-400 mb-4">
                If informal resolution fails, disputes shall be resolved by binding arbitration
                administered by the American Arbitration Association (AAA) under its Commercial
                Arbitration Rules, except that either party may seek injunctive relief in court
                for IP infringement or unauthorized access.
              </p>
              <p className="text-slate-400">
                Class action waiver: You agree that disputes will be resolved individually and
                not as part of any class, consolidated, or representative action.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="governing-law">
              <h2 className="text-2xl font-bold text-white mb-4">14. Governing Law</h2>
              <p className="text-slate-400">
                These Terms shall be governed by the laws of the State of Delaware, United States,
                without regard to its conflict-of-law provisions, except where mandatory local laws
                apply (such as EU consumer protection laws for EU residents).
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="modifications">
              <h2 className="text-2xl font-bold text-white mb-4">15. Modifications to Terms</h2>
              <p className="text-slate-400">
                We reserve the right to modify these Terms at any time. We will provide at least
                30 days&apos; advance notice of material changes via email or an in-platform notification.
                Your continued use of the Service after the effective date of changes constitutes
                acceptance of the revised Terms. If you disagree with changes, you may cancel
                your account before the effective date.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="contact">
              <h2 className="text-2xl font-bold text-white mb-4">16. Contact Information</h2>
              <p className="text-slate-400 mb-6">
                For questions about these Terms, please contact:
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
                  <span className="text-slate-500 text-sm">Legal Contact</span>
                  <p className="text-blue-400">[CONTACT_EMAIL]</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Website</span>
                  <p className="text-blue-400">[WEBSITE_URL]</p>
                </div>
              </div>
              <p className="text-slate-500 text-sm mt-6 text-center">
                By using VidShield AI, you acknowledge that you have read, understood, and agree to be
                bound by these Terms &amp; Conditions.
              </p>
            </section>

          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
