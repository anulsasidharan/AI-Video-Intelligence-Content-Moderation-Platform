import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

export const metadata: Metadata = {
  title: 'GDPR Compliance — VidShield AI',
  description: 'VidShield AI GDPR Compliance — your rights under EU data protection law.',
};

const toc = [
  { id: 'overview', label: '1. Overview' },
  { id: 'legal-basis', label: '2. Legal Basis for Processing' },
  { id: 'data-subjects', label: '3. Data Subject Rights' },
  { id: 'exercising-rights', label: '4. How to Exercise Your Rights' },
  { id: 'retention', label: '5. Data Retention' },
  { id: 'transfers', label: '6. International Data Transfers' },
  { id: 'dpo', label: '7. Data Protection Officer' },
  { id: 'supervisory', label: '8. Supervisory Authority' },
  { id: 'processor', label: '9. Data Processor vs. Controller' },
  { id: 'security', label: '10. Technical & Organisational Measures' },
  { id: 'dpia', label: '11. Data Protection Impact Assessments' },
  { id: 'breach', label: '12. Data Breach Notification' },
  { id: 'contact', label: '13. Contact & DPO Details' },
];

export default function GDPRCompliancePage() {
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
              <ShieldCheck size={14} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Legal</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">GDPR Compliance</h1>
            <p className="text-slate-400 text-lg">
              Last updated: <span className="text-slate-300">[EFFECTIVE_DATE]</span>
            </p>
            <p className="text-slate-400 mt-4 leading-relaxed">
              VidShield AI (&quot;[COMPANY_NAME]&quot;, &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) is committed to
              compliance with the General Data Protection Regulation (EU) 2016/679 (&quot;GDPR&quot;) and
              the UK GDPR. This page explains your rights as a data subject and how we fulfil our
              obligations as a data controller and, where applicable, data processor.
            </p>
          </div>

          {/* GDPR Badge */}
          <div className="grid sm:grid-cols-3 gap-4 mb-10">
            {[
              { label: 'Regulation', value: 'GDPR (EU) 2016/679', sub: 'and UK GDPR' },
              { label: 'Effective', value: '25 May 2018', sub: 'UK GDPR: 31 Jan 2020' },
              { label: 'Our Role', value: 'Data Controller', sub: '+ Processor for clients' },
            ].map((item) => (
              <div key={item.label} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4 text-center">
                <div className="text-slate-500 text-xs uppercase tracking-wider mb-1">{item.label}</div>
                <div className="text-white font-bold text-sm">{item.value}</div>
                <div className="text-slate-500 text-xs mt-0.5">{item.sub}</div>
              </div>
            ))}
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

            <section id="overview">
              <h2 className="text-2xl font-bold text-white mb-4">1. Overview</h2>
              <p className="text-slate-400 mb-4">
                The GDPR grants individuals in the European Economic Area (EEA), UK, and Switzerland
                specific rights over their personal data. VidShield AI processes personal data in
                connection with operating our AI video moderation platform. This document describes:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'The legal basis on which we process your personal data',
                  'Your rights as a data subject and how to exercise them',
                  'How long we retain your data',
                  'How we transfer data internationally with appropriate safeguards',
                  'How to contact our Data Protection Officer',
                  'How to complain to a supervisory authority',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="legal-basis">
              <h2 className="text-2xl font-bold text-white mb-6">2. Legal Basis for Processing</h2>
              <p className="text-slate-400 mb-6">
                Under Article 6 GDPR, we process personal data under the following lawful bases:
              </p>
              <div className="space-y-4">
                {[
                  {
                    article: 'Art. 6(1)(b)',
                    basis: 'Contract Performance',
                    description: 'Processing necessary to provide the VidShield AI service you have subscribed to, including account management, video processing, and billing.',
                    examples: 'Account data, video analysis, payment records',
                  },
                  {
                    article: 'Art. 6(1)(a)',
                    basis: 'Consent',
                    description: 'Where you have given explicit consent for specific processing activities, such as marketing communications and optional analytics cookies.',
                    examples: 'Newsletter subscription, marketing cookies, analytics opt-in',
                  },
                  {
                    article: 'Art. 6(1)(f)',
                    basis: 'Legitimate Interests',
                    description: 'Processing necessary for our legitimate business interests, provided these are not overridden by your fundamental rights.',
                    examples: 'Fraud prevention, security monitoring, product improvement',
                  },
                  {
                    article: 'Art. 6(1)(c)',
                    basis: 'Legal Obligation',
                    description: 'Processing required to comply with applicable laws, including tax regulations, financial record-keeping, and responding to lawful requests.',
                    examples: 'Tax records, regulatory compliance, court orders',
                  },
                ].map((item) => (
                  <div key={item.basis} className="bg-slate-900 border border-slate-800/60 rounded-xl p-5">
                    <div className="flex items-start gap-3 mb-2">
                      <span className="text-xs px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded font-mono flex-shrink-0 mt-0.5">
                        {item.article}
                      </span>
                      <h3 className="text-white font-semibold">{item.basis}</h3>
                    </div>
                    <p className="text-slate-400 text-sm mb-2">{item.description}</p>
                    <p className="text-slate-500 text-xs">
                      <span className="text-slate-400 font-medium">Examples:</span> {item.examples}
                    </p>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 mt-4 text-sm">
                For special category data (Article 9 GDPR), if applicable, we process under explicit
                consent (Art. 9(2)(a)) or other applicable conditions. We do not intentionally collect
                special category data from our platform users.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="data-subjects">
              <h2 className="text-2xl font-bold text-white mb-6">3. Data Subject Rights</h2>
              <p className="text-slate-400 mb-6">
                Under the GDPR, you have the following rights in respect of your personal data:
              </p>
              <div className="space-y-4">
                {[
                  {
                    article: 'Art. 15',
                    right: 'Right of Access',
                    description: 'You have the right to obtain confirmation of whether we process your personal data and, if so, to receive a copy (Subject Access Request — SAR).',
                    timeline: 'Response within 1 month (extendable by 2 months for complex requests)',
                  },
                  {
                    article: 'Art. 16',
                    right: 'Right to Rectification',
                    description: 'You have the right to have inaccurate personal data corrected and incomplete data completed without undue delay.',
                    timeline: 'Response within 1 month',
                  },
                  {
                    article: 'Art. 17',
                    right: 'Right to Erasure ("Right to be Forgotten")',
                    description: 'You have the right to request deletion of your personal data where it is no longer necessary, consent is withdrawn, or processing was unlawful.',
                    timeline: 'Response within 1 month; some data may be retained for legal obligations',
                  },
                  {
                    article: 'Art. 18',
                    right: 'Right to Restriction of Processing',
                    description: 'You have the right to restrict processing while accuracy is contested, for legal claims, or pending a legitimate interests objection.',
                    timeline: 'Restriction applied promptly; response within 1 month',
                  },
                  {
                    article: 'Art. 20',
                    right: 'Right to Data Portability',
                    description: 'You have the right to receive personal data you provided in a structured, commonly used, machine-readable format (e.g., JSON, CSV) and to transmit it to another controller.',
                    timeline: 'Response within 1 month; data provided in standard formats',
                  },
                  {
                    article: 'Art. 21',
                    right: 'Right to Object',
                    description: 'You have the right to object to processing based on legitimate interests or for direct marketing purposes. We must stop unless we have compelling legitimate grounds.',
                    timeline: 'Marketing opt-outs actioned immediately; other objections within 1 month',
                  },
                  {
                    article: 'Art. 22',
                    right: 'Rights re: Automated Decision-Making',
                    description: 'You have the right not to be subject to solely automated decisions with legal or similarly significant effects, and to request human review of such decisions.',
                    timeline: 'Response within 1 month',
                  },
                ].map((item) => (
                  <div key={item.right} className="bg-slate-900 border border-slate-800/60 rounded-xl p-5">
                    <div className="flex items-start gap-3 mb-2">
                      <span className="text-xs px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded font-mono flex-shrink-0 mt-0.5">
                        {item.article}
                      </span>
                      <h3 className="text-white font-semibold">{item.right}</h3>
                    </div>
                    <p className="text-slate-400 text-sm mb-2">{item.description}</p>
                    <p className="text-slate-500 text-xs">
                      <span className="text-slate-400 font-medium">Timeline:</span> {item.timeline}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="exercising-rights">
              <h2 className="text-2xl font-bold text-white mb-6">4. How to Exercise Your Rights</h2>
              <p className="text-slate-400 mb-6">
                To exercise any of your GDPR rights, please contact us using the details below.
                We will respond within <strong className="text-white">one month</strong> and may
                request proof of identity to protect your data.
              </p>

              <div className="grid sm:grid-cols-2 gap-4 mb-6">
                {[
                  { method: 'Email', value: '[DPO_EMAIL]', desc: 'Preferred — fastest response' },
                  { method: 'Postal Mail', value: '[COMPANY_ADDRESS]', desc: 'Attn: Data Protection Officer' },
                  { method: 'In-Platform', value: 'Account Settings → Privacy', desc: 'For data export and deletion' },
                  { method: 'Contact Form', value: '[WEBSITE_URL]/contact', desc: 'Web form available 24/7' },
                ].map((m) => (
                  <div key={m.method} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-slate-500 text-xs uppercase tracking-wider mb-1">{m.method}</div>
                    <div className="text-blue-400 text-sm font-medium mb-0.5">{m.value}</div>
                    <div className="text-slate-500 text-xs">{m.desc}</div>
                  </div>
                ))}
              </div>

              <div className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                <p className="text-white font-semibold text-sm mb-2">What to include in your request</p>
                <ul className="space-y-1">
                  {[
                    'Your full name and email address registered on VidShield AI',
                    'The specific right(s) you wish to exercise',
                    'Any relevant details (e.g., specific data categories for portability requests)',
                    'A copy of a valid identity document if requested for verification',
                  ].map((item) => (
                    <li key={item} className="flex gap-3 text-sm">
                      <span className="text-blue-400 mt-0.5 flex-shrink-0">•</span>
                      <span className="text-slate-400">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="retention">
              <h2 className="text-2xl font-bold text-white mb-6">5. Data Retention</h2>
              <p className="text-slate-400 mb-6">
                We retain personal data only for as long as necessary for the purposes for which
                it was collected, or as required by law. Our retention schedule:
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800/60">
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Data Category</th>
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Retention Period</th>
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Legal Basis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {[
                      ['Account & profile data', 'Active account + 30 days post-deletion', 'Contract'],
                      ['Video content & analysis', 'Configurable (default 90 days)', 'Contract'],
                      ['Moderation reports', '12 months (enterprise: configurable)', 'Contract / Legitimate Interest'],
                      ['Billing & invoice records', '7 years', 'Legal Obligation (tax law)'],
                      ['Access & security logs', '90 days', 'Legitimate Interest'],
                      ['Support communications', '3 years', 'Legitimate Interest'],
                      ['Consent records', '5 years after consent expires', 'Legal Obligation'],
                      ['DSAR correspondence', '3 years after resolution', 'Legal Obligation'],
                    ].map(([category, period, basis]) => (
                      <tr key={category} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-3 text-slate-300">{category}</td>
                        <td className="px-5 py-3 text-slate-400">{period}</td>
                        <td className="px-5 py-3 text-slate-500 text-xs">{basis}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-slate-400 mt-4 text-sm">
                After the retention period, data is securely deleted or anonymised. You may request
                earlier deletion subject to applicable legal obligations.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="transfers">
              <h2 className="text-2xl font-bold text-white mb-6">6. International Data Transfers</h2>
              <p className="text-slate-400 mb-4">
                VidShield AI is operated from the United States. When personal data from the EEA,
                UK, or Switzerland is transferred to the US or other third countries, we rely on
                the following safeguards (Article 46 GDPR):
              </p>
              <div className="space-y-4 mb-6">
                {[
                  {
                    mechanism: 'Standard Contractual Clauses (SCCs)',
                    detail: 'EU Commission-approved SCCs (2021 version) are in place with all US-based processors, including AWS, OpenAI, and Sentry.',
                    applies: 'EEA → US transfers',
                  },
                  {
                    mechanism: 'UK International Data Transfer Agreements (IDTAs)',
                    detail: 'UK ICO-approved IDTAs supplement our SCCs for transfers originating from the UK.',
                    applies: 'UK → non-UK transfers',
                  },
                  {
                    mechanism: 'Adequacy Decisions',
                    detail: 'Where the European Commission has issued an adequacy decision for a recipient country, transfers rely on that decision.',
                    applies: 'EEA → adequate countries',
                  },
                ].map((item) => (
                  <div key={item.mechanism} className="bg-slate-900 border border-slate-800/60 rounded-xl p-5">
                    <h3 className="text-white font-semibold text-sm mb-1">{item.mechanism}</h3>
                    <p className="text-slate-400 text-sm mb-2">{item.detail}</p>
                    <span className="text-xs px-2 py-0.5 bg-green-500/10 border border-green-500/20 text-green-400 rounded">
                      {item.applies}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 text-sm">
                Copies of our SCCs and IDTAs are available on request by contacting{' '}
                <span className="text-blue-400">[DPO_EMAIL]</span>.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="dpo">
              <h2 className="text-2xl font-bold text-white mb-6">7. Data Protection Officer</h2>
              <p className="text-slate-400 mb-6">
                We have appointed a Data Protection Officer (DPO) responsible for overseeing
                our data protection strategy and ensuring compliance with the GDPR.
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 space-y-3">
                <div>
                  <span className="text-slate-500 text-sm">Role</span>
                  <p className="text-white font-semibold">Data Protection Officer</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Organisation</span>
                  <p className="text-slate-300">VidShield AI ([COMPANY_NAME])</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">DPO Email</span>
                  <p className="text-blue-400">[DPO_EMAIL]</p>
                </div>
                <div>
                  <span className="text-slate-500 text-sm">Postal Address</span>
                  <p className="text-slate-300">[COMPANY_ADDRESS]<br />Attn: Data Protection Officer</p>
                </div>
              </div>
              <p className="text-slate-400 mt-4 text-sm">
                The DPO operates independently and is not subject to instructions from management
                regarding the exercise of their tasks. You may contact the DPO directly for any
                GDPR-related concerns.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="supervisory">
              <h2 className="text-2xl font-bold text-white mb-6">8. Supervisory Authority</h2>
              <p className="text-slate-400 mb-4">
                You have the right to lodge a complaint with a supervisory authority if you believe
                we have processed your personal data in breach of the GDPR (Article 77 GDPR).
                You may contact:
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  {
                    authority: 'Your Local DPA',
                    detail: 'You may complain to the supervisory authority in your EU Member State of habitual residence, place of work, or place of the alleged breach.',
                    link: 'edpb.europa.eu',
                  },
                  {
                    authority: 'UK — ICO',
                    detail: 'Information Commissioner\'s Office (UK) for UK residents.',
                    link: 'ico.org.uk',
                  },
                  {
                    authority: 'Ireland — DPC',
                    detail: 'Data Protection Commission — lead supervisory authority for VidShield AI\'s EU operations.',
                    link: 'dataprotection.ie',
                  },
                  {
                    authority: 'Switzerland — FDPIC',
                    detail: 'Federal Data Protection and Information Commissioner for Swiss residents.',
                    link: 'edoeb.admin.ch',
                  },
                ].map((item) => (
                  <div key={item.authority} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-white font-semibold text-sm mb-1">{item.authority}</div>
                    <p className="text-slate-400 text-xs mb-2">{item.detail}</p>
                    <span className="text-blue-400 text-xs">{item.link}</span>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 mt-4 text-sm">
                We encourage you to contact us first at{' '}
                <span className="text-blue-400">[DPO_EMAIL]</span> — we aim to resolve all concerns
                fairly and promptly.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="processor">
              <h2 className="text-2xl font-bold text-white mb-6">9. Data Processor vs. Controller</h2>
              <div className="grid sm:grid-cols-2 gap-4 mb-4">
                <div className="bg-slate-900 border border-blue-500/20 rounded-xl p-5">
                  <div className="text-blue-400 font-semibold text-sm mb-2">Data Controller</div>
                  <p className="text-slate-400 text-sm mb-3">
                    When you use VidShield AI directly (account registration, billing, platform usage),
                    we act as the <strong className="text-white">data controller</strong> — we determine
                    the purposes and means of processing your personal data.
                  </p>
                  <span className="text-xs px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded">
                    Applies to: VidShield AI platform users
                  </span>
                </div>
                <div className="bg-slate-900 border border-purple-500/20 rounded-xl p-5">
                  <div className="text-purple-400 font-semibold text-sm mb-2">Data Processor</div>
                  <p className="text-slate-400 text-sm mb-3">
                    When enterprise clients submit content for moderation, we act as a{' '}
                    <strong className="text-white">data processor</strong> on behalf of the client
                    (who is the data controller for their end-users&apos; data).
                  </p>
                  <span className="text-xs px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded">
                    Applies to: Enterprise client video data
                  </span>
                </div>
              </div>
              <p className="text-slate-400 text-sm">
                Enterprise clients may request a Data Processing Agreement (DPA) under Article 28 GDPR
                by contacting <span className="text-blue-400">[DPO_EMAIL]</span>.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="security">
              <h2 className="text-2xl font-bold text-white mb-6">10. Technical &amp; Organisational Measures</h2>
              <p className="text-slate-400 mb-6">
                We implement appropriate technical and organisational measures (Article 32 GDPR)
                to ensure security appropriate to the risk:
              </p>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  { category: 'Encryption', items: ['TLS 1.3 in transit', 'AES-256 at rest', 'Encrypted backups'] },
                  { category: 'Access Control', items: ['Role-based access (RBAC)', 'MFA for admin accounts', 'Principle of least privilege'] },
                  { category: 'Monitoring', items: ['24/7 intrusion detection', 'Automated anomaly alerts', 'Centralised audit logs'] },
                  { category: 'Organisational', items: ['Annual security training', 'Background-checked personnel', 'Data minimisation by design'] },
                  { category: 'Resilience', items: ['Multi-AZ AWS deployment', 'Automated failover', 'Regular DR testing'] },
                  { category: 'Vendor Management', items: ['DPA with all processors', 'Annual vendor reviews', 'Sub-processor registry'] },
                ].map((group) => (
                  <div key={group.category} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-white font-semibold text-sm mb-2">{group.category}</div>
                    <ul className="space-y-1">
                      {group.items.map((item) => (
                        <li key={item} className="flex gap-2 text-xs">
                          <span className="text-green-400 mt-0.5 flex-shrink-0">✓</span>
                          <span className="text-slate-400">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="dpia">
              <h2 className="text-2xl font-bold text-white mb-4">11. Data Protection Impact Assessments</h2>
              <p className="text-slate-400 mb-4">
                We conduct Data Protection Impact Assessments (DPIAs) under Article 35 GDPR before
                introducing new processing activities that are likely to result in a high risk to
                individuals&apos; rights and freedoms, including:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'Large-scale processing of sensitive video content',
                  'New AI model deployments that involve profiling',
                  'Introduction of new third-party processors',
                  'Significant changes to data flows or retention policies',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="breach">
              <h2 className="text-2xl font-bold text-white mb-4">12. Data Breach Notification</h2>
              <p className="text-slate-400 mb-4">
                In the event of a personal data breach (Article 33–34 GDPR), we will:
              </p>
              <div className="space-y-3">
                {[
                  { step: '1', action: 'Notify the lead supervisory authority within 72 hours of becoming aware of the breach (where feasible).' },
                  { step: '2', action: 'Assess the risk to individuals\' rights and freedoms using our incident response framework.' },
                  { step: '3', action: 'Notify affected individuals without undue delay if the breach is likely to result in high risk to their rights.' },
                  { step: '4', action: 'Document all breaches in our internal breach register, regardless of whether notification is required.' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4 bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="w-7 h-7 bg-blue-500/10 border border-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-blue-400 text-xs font-bold">{item.step}</span>
                    </div>
                    <p className="text-slate-400 text-sm pt-1">{item.action}</p>
                  </div>
                ))}
              </div>
              <p className="text-slate-400 mt-4 text-sm">
                If you suspect a security incident affecting your account, contact us immediately at{' '}
                <span className="text-blue-400">[DPO_EMAIL]</span>.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="contact">
              <h2 className="text-2xl font-bold text-white mb-6">13. Contact &amp; DPO Details</h2>
              <p className="text-slate-400 mb-6">
                For GDPR-related enquiries, data subject requests, or to request a Data Processing
                Agreement:
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <span className="text-slate-500 text-sm">Company</span>
                    <p className="text-white font-semibold">VidShield AI ([COMPANY_NAME])</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-sm">Registered Address</span>
                    <p className="text-slate-300">[COMPANY_ADDRESS]</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-sm">DPO Email</span>
                    <p className="text-blue-400">[DPO_EMAIL]</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-sm">General Contact</span>
                    <p className="text-blue-400">[CONTACT_EMAIL]</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/legal/privacy-policy"
                  className="flex-1 text-center bg-slate-900 border border-slate-800/60 hover:border-slate-700 text-slate-300 text-sm px-4 py-3 rounded-xl transition-colors"
                >
                  Privacy Policy
                </Link>
                <Link
                  href="/legal/cookie-policy"
                  className="flex-1 text-center bg-slate-900 border border-slate-800/60 hover:border-slate-700 text-slate-300 text-sm px-4 py-3 rounded-xl transition-colors"
                >
                  Cookie Policy
                </Link>
                <Link
                  href="/legal/terms-conditions"
                  className="flex-1 text-center bg-slate-900 border border-slate-800/60 hover:border-slate-700 text-slate-300 text-sm px-4 py-3 rounded-xl transition-colors"
                >
                  Terms &amp; Conditions
                </Link>
              </div>
            </section>

          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
