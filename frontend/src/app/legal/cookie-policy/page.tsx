import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, Cookie } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

export const metadata: Metadata = {
  title: 'Cookie Policy — VidShield AI',
  description: 'VidShield AI Cookie Policy — how we use cookies and how to manage them.',
};

const toc = [
  { id: 'what-are-cookies', label: '1. What Are Cookies?' },
  { id: 'why-we-use', label: '2. Why We Use Cookies' },
  { id: 'types', label: '3. Types of Cookies We Use' },
  { id: 'cookie-list', label: '4. Cookie Reference List' },
  { id: 'third-party', label: '5. Third-Party Cookies' },
  { id: 'managing', label: '6. Managing Your Cookie Preferences' },
  { id: 'impact', label: '7. Impact of Disabling Cookies' },
  { id: 'updates', label: '8. Updates to This Policy' },
  { id: 'contact', label: '9. Contact Us' },
];

const cookieTypes = [
  {
    type: 'Essential',
    color: 'blue',
    icon: '🔒',
    description: 'Required for the platform to function. Cannot be disabled.',
    canDisable: false,
    examples: ['Authentication tokens', 'Session identifiers', 'CSRF protection tokens', 'Load balancer cookies'],
  },
  {
    type: 'Performance & Analytics',
    color: 'purple',
    icon: '📊',
    description: 'Help us understand how visitors use our platform so we can improve it.',
    canDisable: true,
    examples: ['Page view counts', 'Feature usage tracking', 'Error rate monitoring', 'Session duration'],
  },
  {
    type: 'Functional / Preferences',
    color: 'green',
    icon: '⚙️',
    description: 'Remember your settings and preferences across visits.',
    canDisable: true,
    examples: ['UI theme preference', 'Language/locale settings', 'Dashboard layout', 'Notification preferences'],
  },
  {
    type: 'Marketing',
    color: 'amber',
    icon: '📣',
    description: 'Used to deliver relevant advertisements and measure campaign effectiveness.',
    canDisable: true,
    examples: ['Ad impression tracking', 'Conversion attribution', 'Retargeting identifiers'],
  },
];

const cookieList = [
  { name: 'vs_session', purpose: 'Maintains your authenticated session', duration: 'Session', type: 'Essential', party: '1st' },
  { name: 'vs_auth_token', purpose: 'Stores encrypted authentication credential', duration: '30 days', type: 'Essential', party: '1st' },
  { name: 'vs_csrf', purpose: 'Prevents cross-site request forgery attacks', duration: 'Session', type: 'Essential', party: '1st' },
  { name: 'vs_prefs', purpose: 'Stores UI theme and dashboard layout preferences', duration: '1 year', type: 'Functional', party: '1st' },
  { name: 'vs_locale', purpose: 'Remembers your language and region setting', duration: '1 year', type: 'Functional', party: '1st' },
  { name: '_ga', purpose: 'Google Analytics — distinguishes unique users', duration: '2 years', type: 'Analytics', party: '3rd' },
  { name: '_ga_*', purpose: 'Google Analytics — stores session state', duration: '2 years', type: 'Analytics', party: '3rd' },
  { name: '_gid', purpose: 'Google Analytics — identifies user session', duration: '24 hours', type: 'Analytics', party: '3rd' },
  { name: 'sentry_session', purpose: 'Sentry — correlates error reports with sessions', duration: 'Session', type: 'Analytics', party: '3rd' },
  { name: 'stripe_mid', purpose: 'Stripe — fraud prevention and checkout flow', duration: '1 year', type: 'Essential', party: '3rd' },
  { name: 'intercom-*', purpose: 'Intercom — in-app chat and support widget', duration: '9 months', type: 'Functional', party: '3rd' },
];

const typeColorMap: Record<string, string> = {
  Essential: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  Analytics: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  Functional: 'bg-green-500/10 text-green-400 border-green-500/20',
  Marketing: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
};

export default function CookiePolicyPage() {
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
              <Cookie size={14} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Legal</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">Cookie Policy</h1>
            <p className="text-slate-400 text-lg">
              Last updated: <span className="text-slate-300">[EFFECTIVE_DATE]</span>
            </p>
            <p className="text-slate-400 mt-4 leading-relaxed">
              This Cookie Policy explains how VidShield AI (&quot;[COMPANY_NAME]&quot;, &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;)
              uses cookies and similar tracking technologies on{' '}
              <span className="text-blue-400">[WEBSITE_URL]</span>. This policy should be read
              alongside our{' '}
              <Link href="/legal/privacy-policy" className="text-blue-400 hover:text-blue-300 transition-colors">
                Privacy Policy
              </Link>.
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

            <section id="what-are-cookies">
              <h2 className="text-2xl font-bold text-white mb-4">1. What Are Cookies?</h2>
              <p className="text-slate-400 mb-4">
                Cookies are small text files placed on your device (computer, tablet, or phone) by
                websites you visit. They are widely used to make websites work efficiently, remember
                your preferences, and provide information to website owners.
              </p>
              <p className="text-slate-400 mb-4">
                Besides cookies, we may use similar technologies such as:
              </p>
              <ul className="space-y-2 ml-4">
                {[
                  'Local Storage — stores data in your browser beyond a single session',
                  'Session Storage — temporary storage cleared when you close the browser tab',
                  'Web Beacons / Pixels — tiny images used to track email opens and page visits',
                  'Fingerprinting — device characteristic data used for fraud prevention (not tracking)',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="why-we-use">
              <h2 className="text-2xl font-bold text-white mb-4">2. Why We Use Cookies</h2>
              <p className="text-slate-400 mb-4">We use cookies to:</p>
              <ul className="space-y-2 ml-4">
                {[
                  'Keep you signed in securely across page loads',
                  'Remember your account settings and UI preferences',
                  'Understand how users navigate and use the platform',
                  'Identify and fix technical errors quickly',
                  'Measure the effectiveness of marketing campaigns',
                  'Protect against fraud and unauthorized access',
                  'Comply with legal and regulatory requirements',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="text-blue-400 mt-1 flex-shrink-0">•</span>
                    <span className="text-slate-400">{item}</span>
                  </li>
                ))}
              </ul>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="types">
              <h2 className="text-2xl font-bold text-white mb-6">3. Types of Cookies We Use</h2>
              <div className="space-y-5">
                {cookieTypes.map((ct) => (
                  <div key={ct.type} className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{ct.icon}</span>
                        <h3 className="text-white font-semibold text-lg">{ct.type} Cookies</h3>
                      </div>
                      <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
                        ct.canDisable
                          ? 'bg-slate-800 text-slate-400 border-slate-700'
                          : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      }`}>
                        {ct.canDisable ? 'Optional' : 'Required'}
                      </span>
                    </div>
                    <p className="text-slate-400 text-sm mb-4">{ct.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {ct.examples.map((ex) => (
                        <span key={ex} className="text-xs px-3 py-1 bg-slate-800 border border-slate-700/50 text-slate-400 rounded-full">
                          {ex}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="cookie-list">
              <h2 className="text-2xl font-bold text-white mb-6">4. Cookie Reference List</h2>
              <p className="text-slate-400 mb-6">
                The following table lists the specific cookies currently in use on VidShield AI:
              </p>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-800/60">
                        <th className="text-left text-slate-400 font-medium px-4 py-3">Cookie Name</th>
                        <th className="text-left text-slate-400 font-medium px-4 py-3">Purpose</th>
                        <th className="text-left text-slate-400 font-medium px-4 py-3">Duration</th>
                        <th className="text-left text-slate-400 font-medium px-4 py-3">Type</th>
                        <th className="text-left text-slate-400 font-medium px-4 py-3">Party</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {cookieList.map((cookie) => (
                        <tr key={cookie.name} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-4 py-3 font-mono text-blue-300 text-xs">{cookie.name}</td>
                          <td className="px-4 py-3 text-slate-400">{cookie.purpose}</td>
                          <td className="px-4 py-3 text-slate-400 whitespace-nowrap">{cookie.duration}</td>
                          <td className="px-4 py-3">
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${typeColorMap[cookie.type] ?? 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                              {cookie.type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400 text-xs">{cookie.party}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <p className="text-slate-500 text-xs mt-3">
                This list is updated periodically. &quot;1st&quot; = first-party (set by VidShield AI),
                &quot;3rd&quot; = third-party (set by external service providers).
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="third-party">
              <h2 className="text-2xl font-bold text-white mb-6">5. Third-Party Cookies</h2>
              <p className="text-slate-400 mb-6">
                Some cookies are set by third-party services we use. These providers have their own
                privacy policies:
              </p>
              <div className="space-y-4">
                {[
                  {
                    provider: 'Google Analytics',
                    purpose: 'Web analytics — measures visitor behavior and platform usage patterns.',
                    link: 'https://policies.google.com/privacy',
                    optOut: 'https://tools.google.com/dlpage/gaoptout',
                  },
                  {
                    provider: 'Stripe',
                    purpose: 'Payment processing and fraud prevention for subscription billing.',
                    link: 'https://stripe.com/privacy',
                    optOut: null,
                  },
                  {
                    provider: 'Sentry',
                    purpose: 'Application error monitoring and performance tracking.',
                    link: 'https://sentry.io/privacy/',
                    optOut: null,
                  },
                  {
                    provider: 'Intercom',
                    purpose: 'Customer support chat widget and in-app messaging.',
                    link: 'https://www.intercom.com/legal/privacy',
                    optOut: null,
                  },
                ].map((tp) => (
                  <div key={tp.provider} className="bg-slate-900 border border-slate-800/60 rounded-xl p-4">
                    <div className="text-white font-semibold text-sm mb-1">{tp.provider}</div>
                    <p className="text-slate-400 text-sm mb-2">{tp.purpose}</p>
                    <div className="flex gap-4 text-xs">
                      <span className="text-slate-500">Privacy: <span className="text-blue-400">{tp.link}</span></span>
                      {tp.optOut && <span className="text-slate-500">Opt-out: <span className="text-blue-400">{tp.optOut}</span></span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="managing">
              <h2 className="text-2xl font-bold text-white mb-6">6. Managing Your Cookie Preferences</h2>

              <h3 className="text-lg font-semibold text-white mb-3">6.1 Cookie Consent Banner</h3>
              <p className="text-slate-400 mb-6">
                On your first visit, we display a cookie consent banner. You can accept all cookies,
                reject optional cookies, or customize your preferences. You can change your preferences
                at any time via the &quot;Cookie Settings&quot; link in the footer.
              </p>

              <h3 className="text-lg font-semibold text-white mb-3">6.2 Browser Settings</h3>
              <p className="text-slate-400 mb-4">
                Most browsers allow you to control cookies through their settings. Here is how to manage
                cookies in popular browsers:
              </p>
              <div className="grid sm:grid-cols-2 gap-3 mb-4">
                {[
                  { browser: 'Google Chrome', path: 'Settings → Privacy and security → Cookies' },
                  { browser: 'Mozilla Firefox', path: 'Options → Privacy & Security → Cookies' },
                  { browser: 'Safari', path: 'Preferences → Privacy → Manage Website Data' },
                  { browser: 'Microsoft Edge', path: 'Settings → Cookies and site permissions' },
                ].map((b) => (
                  <div key={b.browser} className="bg-slate-900 border border-slate-800/60 rounded-xl p-3">
                    <div className="text-white font-medium text-sm mb-0.5">{b.browser}</div>
                    <p className="text-slate-500 text-xs">{b.path}</p>
                  </div>
                ))}
              </div>

              <h3 className="text-lg font-semibold text-white mb-3">6.3 Google Analytics Opt-Out</h3>
              <p className="text-slate-400">
                Install the{' '}
                <span className="text-blue-400">Google Analytics Opt-out Browser Add-on</span>{' '}
                to prevent your data from being collected by Google Analytics across all websites.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="impact">
              <h2 className="text-2xl font-bold text-white mb-6">7. Impact of Disabling Cookies</h2>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6">
                <p className="text-amber-300 text-sm font-semibold mb-1">Important</p>
                <p className="text-amber-200/70 text-sm">
                  Disabling essential cookies will prevent VidShield AI from functioning correctly.
                  You will be unable to log in or use the platform.
                </p>
              </div>
              <div className="bg-slate-900 border border-slate-800/60 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800/60">
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Cookie Type</th>
                      <th className="text-left text-slate-400 font-medium px-5 py-3">Impact if Disabled</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40">
                    {[
                      ['Essential', 'Platform will not work — login and core functionality unavailable'],
                      ['Analytics', 'We cannot track usage; platform still functions normally'],
                      ['Functional', 'Preferences not saved; you may need to reconfigure on each visit'],
                      ['Marketing', 'Ads may be less relevant; no other platform impact'],
                    ].map(([type, impact]) => (
                      <tr key={type}>
                        <td className="px-5 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${typeColorMap[type] ?? 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                            {type}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-slate-400">{impact}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="updates">
              <h2 className="text-2xl font-bold text-white mb-4">8. Updates to This Policy</h2>
              <p className="text-slate-400">
                We may update this Cookie Policy periodically to reflect changes in our practices or
                applicable law. We will update the &quot;Last updated&quot; date at the top of this page.
                For significant changes, we will notify you via the cookie consent banner or email.
              </p>
            </section>

            <div className="border-t border-slate-800/60" />

            <section id="contact">
              <h2 className="text-2xl font-bold text-white mb-4">9. Contact Us</h2>
              <p className="text-slate-400 mb-6">
                If you have questions about our use of cookies, please contact:
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
              </div>
            </section>

          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
