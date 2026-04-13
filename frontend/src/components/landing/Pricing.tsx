import Link from 'next/link';
import { Check, Zap } from 'lucide-react';

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: '/month',
    description: 'Get started with basic AI video moderation at no cost.',
    highlight: false,
    badge: null,
    trialNote: null,
    features: [
      'Up to 10 videos / month',
      'Standard AI moderation',
      'Basic content reports',
      'Email support',
      'REST API access',
    ],
    cta: 'Get Started Free',
    ctaHref: '/register',
  },
  {
    name: 'Starter',
    price: '$299',
    period: '/month',
    description: 'Perfect for small platforms getting started with AI moderation.',
    highlight: false,
    badge: null,
    trialNote: '14-day free trial',
    features: [
      '10,000 video minutes / month',
      '3 moderation policies',
      'Upload & API ingestion',
      'Standard content categories',
      'Webhook notifications',
      'REST API access',
      '7-day report retention',
      'Email support',
    ],
    cta: 'Start Free Trial',
    ctaHref: '/register',
  },
  {
    name: 'Growth',
    price: '$999',
    period: '/month',
    description: 'For scaling platforms with high-volume video and live stream needs.',
    highlight: true,
    badge: 'Most Popular',
    trialNote: '14-day free trial',
    features: [
      '100,000 video minutes / month',
      'Unlimited moderation policies',
      'Upload, Live Stream & API',
      'All content categories + custom',
      'Webhooks + WebSocket',
      'Full REST API + analytics export',
      '90-day report retention',
      'Human review queue',
      'Priority support + SLA',
    ],
    cta: 'Start Free Trial',
    ctaHref: '/register',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large platforms, regulated industries, and custom deployment needs.',
    highlight: false,
    badge: null,
    trialNote: null,
    features: [
      'Unlimited video minutes',
      'Custom AI model fine-tuning',
      'Multi-tenant architecture',
      'Custom compliance reporting',
      'Dedicated infrastructure',
      'SSO / SAML integration',
      'Unlimited retention',
      'SLA-backed uptime guarantee',
      '24/7 dedicated support',
    ],
    cta: 'Contact Sales',
    ctaHref: 'mailto:sales@orionvexa.ca?subject=VidShield%20Enterprise%20Enquiry',
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="bg-slate-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">Pricing</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Simple, transparent pricing
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Start free — no credit card required. Upgrade anytime.
            Paid plans include a 14-day free trial.
          </p>
        </div>

        {/* Plans */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl border p-7 transition-all duration-200 ${
                plan.highlight
                  ? 'bg-blue-600/10 border-blue-500/50 shadow-xl shadow-blue-900/20'
                  : 'bg-slate-900/60 border-slate-800/60 hover:border-slate-700'
              }`}
            >
              {/* Popular badge */}
              {plan.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1.5 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow">
                    <Zap size={11} />
                    {plan.badge}
                  </span>
                </div>
              )}

              {/* Plan name & price */}
              <div className="mb-6">
                <div className="text-slate-300 font-semibold text-sm mb-3">{plan.name}</div>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-white text-4xl font-extrabold">{plan.price}</span>
                  {plan.period && (
                    <span className="text-slate-400 text-sm font-medium">{plan.period}</span>
                  )}
                </div>
                {plan.trialNote && (
                  <p className="text-green-400 text-xs font-medium mb-2">{plan.trialNote} · no card required</p>
                )}
                <p className="text-slate-500 text-sm">{plan.description}</p>
              </div>

              {/* Features */}
              <ul className="space-y-3 flex-1 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <Check
                      size={15}
                      className={`mt-0.5 flex-shrink-0 ${
                        plan.highlight ? 'text-blue-400' : 'text-green-400'
                      }`}
                    />
                    <span className="text-slate-300 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Link
                href={plan.ctaHref}
                className={`w-full text-center py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
                  plan.highlight
                    ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/25'
                    : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700/60'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Bottom note */}
        <p className="text-center text-slate-500 text-sm mt-10">
          Free plan forever · Paid plans include 14-day free trial · No credit card required · Cancel anytime
        </p>
      </div>
    </section>
  );
}
