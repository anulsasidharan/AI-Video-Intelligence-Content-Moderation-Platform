import { Star, TrendingDown, Zap, ShieldCheck } from 'lucide-react';

const testimonials = [
  {
    quote:
      'We went from a 48-hour moderation backlog to real-time analysis overnight. VidShield AI cut our manual review team workload by 87% in the first month.',
    author: 'Head of Trust & Safety',
    company: 'Large EdTech Platform',
    industry: 'EdTech',
    metric: '87% reduction in manual reviews',
  },
  {
    quote:
      'The policy editor is a game-changer. We configure new content categories in minutes without touching code — something that used to take weeks of ML retraining.',
    author: 'VP of Product',
    company: 'Social Video Startup',
    industry: 'Social Media',
    metric: 'New policies deployed in <10 minutes',
  },
  {
    quote:
      'Accuracy went from 76% with our old keyword filters to 99.4% with VidShield. False positives dropped dramatically, and our creators are happier.',
    author: 'Engineering Lead',
    company: 'Video Streaming Platform',
    industry: 'Video Platform',
    metric: '99.4% moderation accuracy',
  },
];

const impactStats = [
  {
    icon: TrendingDown,
    value: '87%',
    label: 'Reduction in manual review hours',
    description: 'Average across customer deployments',
    color: 'text-green-400',
    bg: 'bg-green-600/10 border-green-500/20',
  },
  {
    icon: Zap,
    value: '1.8s',
    label: 'Average time to moderation report',
    description: 'From video submission to full report',
    color: 'text-blue-400',
    bg: 'bg-blue-600/10 border-blue-500/20',
  },
  {
    icon: ShieldCheck,
    value: '99.4%',
    label: 'Moderation accuracy rate',
    description: 'Validated on industry benchmark datasets',
    color: 'text-violet-400',
    bg: 'bg-violet-600/10 border-violet-500/20',
  },
  {
    icon: TrendingDown,
    value: '23x',
    label: 'Faster than manual review',
    description: 'Measured against average human review time',
    color: 'text-orange-400',
    bg: 'bg-orange-600/10 border-orange-500/20',
  },
];

const trustedBy = [
  'Video Platforms',
  'EdTech Companies',
  'Social Networks',
  'Enterprise Media',
  'Surveillance Ops',
  'Content Agencies',
];

export function SocialProof() {
  return (
    <section id="social-proof" className="bg-slate-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <Star size={14} className="text-blue-400 fill-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Proven Results</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Real impact, measurable results
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Platforms using VidShield AI consistently report dramatic reductions in moderation cost,
            time, and error rate — from day one.
          </p>
        </div>

        {/* Impact metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-16">
          {impactStats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                className={`bg-slate-950/60 border rounded-2xl p-5 ${stat.bg}`}
              >
                <div
                  className={`w-10 h-10 rounded-xl border flex items-center justify-center mb-4 ${stat.bg}`}
                >
                  <Icon size={18} className={stat.color} />
                </div>
                <div className={`text-3xl font-extrabold mb-1 ${stat.color}`}>{stat.value}</div>
                <div className="text-white font-semibold text-sm mb-1">{stat.label}</div>
                <div className="text-slate-500 text-xs">{stat.description}</div>
              </div>
            );
          })}
        </div>

        {/* Testimonials */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {testimonials.map((t) => (
            <div
              key={t.author}
              className="bg-slate-950/60 border border-slate-800/60 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors"
            >
              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} size={14} className="text-yellow-400 fill-yellow-400" />
                ))}
              </div>

              {/* Quote */}
              <blockquote className="text-slate-300 text-sm leading-relaxed mb-5 flex-1">
                &ldquo;{t.quote}&rdquo;
              </blockquote>

              {/* Impact metric pill */}
              <div className="inline-flex items-center gap-1.5 bg-green-600/10 border border-green-500/20 rounded-full px-3 py-1 mb-5 w-fit">
                <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                <span className="text-green-300 text-xs font-medium">{t.metric}</span>
              </div>

              {/* Author */}
              <div className="pt-4 border-t border-slate-800/60">
                <div className="text-white font-semibold text-sm">{t.author}</div>
                <div className="text-slate-500 text-xs">
                  {t.company} · {t.industry}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Trusted by industries */}
        <div className="text-center">
          <div className="text-slate-500 text-sm font-medium mb-5">
            Trusted across industries
          </div>
          <div className="flex flex-wrap gap-3 justify-center">
            {trustedBy.map((industry) => (
              <span
                key={industry}
                className="text-xs px-4 py-2 bg-slate-800 border border-slate-700/60 text-slate-400 rounded-full font-medium"
              >
                {industry}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
