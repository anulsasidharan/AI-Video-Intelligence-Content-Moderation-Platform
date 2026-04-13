import Link from 'next/link';
import { AlertTriangle, Clock, DollarSign, TrendingUp, ArrowRight } from 'lucide-react';

const painPoints = [
  {
    icon: Clock,
    stat: '72 hours',
    label: 'Average manual review backlog',
    description:
      'Platforms relying on human moderators face multi-day review queues, letting harmful content stay live while violating their own policies.',
  },
  {
    icon: DollarSign,
    stat: '$1.4M+',
    label: 'Annual cost of manual moderation teams',
    description:
      'Mid-size platforms spend millions staffing around-the-clock content review teams — a cost that scales linearly with content volume.',
  },
  {
    icon: AlertTriangle,
    stat: '23%',
    label: 'False-positive rate in rule-based filters',
    description:
      'Keyword and rule-based tools misclassify nearly 1 in 4 pieces of content — over-blocking legitimate content and missing nuanced violations.',
  },
  {
    icon: TrendingUp,
    stat: '500%',
    label: 'Video upload growth since 2020',
    description:
      'Content volume has exploded — legacy moderation infrastructure simply cannot keep up, creating safety, legal, and reputational risk.',
  },
];

const gaps = [
  {
    label: 'Slow',
    description: 'Manual human review takes hours to days — harmful content stays live.',
  },
  {
    label: 'Expensive',
    description: 'Staffing moderation teams at scale is cost-prohibitive for most platforms.',
  },
  {
    label: 'Inaccurate',
    description: 'Rule-based filters miss context, nuance, and multi-modal violations.',
  },
  {
    label: 'Rigid',
    description: 'Existing tools cannot adapt to new content categories without re-engineering.',
  },
];

export function ProblemStatement() {
  return (
    <section id="problem" className="bg-slate-950 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-red-600/10 border border-red-500/20 rounded-full px-4 py-1.5 mb-4">
            <AlertTriangle size={14} className="text-red-400" />
            <span className="text-red-400 text-sm font-medium">The Problem</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4 leading-tight">
            Video content moderation is broken —{' '}
            <span className="text-red-400">and getting worse</span>
          </h2>
          <p className="text-slate-400 text-lg max-w-3xl mx-auto">
            Every video platform faces the same crisis: content volume is exploding while moderation
            infrastructure stays stuck in 2015. The result? Harmful content goes live, communities
            suffer, and platforms face regulatory and reputational fallout.
          </p>
        </div>

        {/* Pain point cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-16">
          {painPoints.map((point) => {
            const Icon = point.icon;
            return (
              <div
                key={point.label}
                className="bg-slate-900/70 border border-red-900/30 rounded-2xl p-6 hover:border-red-800/50 transition-colors"
              >
                <div className="w-10 h-10 bg-red-600/10 border border-red-500/20 rounded-xl flex items-center justify-center mb-4">
                  <Icon size={18} className="text-red-400" />
                </div>
                <div className="text-3xl font-extrabold text-red-400 mb-1">{point.stat}</div>
                <div className="text-white font-semibold text-sm mb-2">{point.label}</div>
                <p className="text-slate-500 text-xs leading-relaxed">{point.description}</p>
              </div>
            );
          })}
        </div>

        {/* Why existing solutions fail */}
        <div className="bg-slate-900/60 border border-slate-800/60 rounded-2xl p-8 mb-12">
          <div className="text-center mb-8">
            <h3 className="text-white font-bold text-xl mb-2">
              Why existing solutions fall short
            </h3>
            <p className="text-slate-400 text-sm">
              Manual review teams, keyword filters, and basic ML classifiers all fail in the same ways.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {gaps.map((gap) => (
              <div key={gap.label} className="flex flex-col gap-2">
                <div className="inline-flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-red-600/20 border border-red-500/30 flex items-center justify-center flex-shrink-0">
                    <span className="text-red-400 text-xs font-bold">✗</span>
                  </div>
                  <span className="text-white font-semibold text-sm">{gap.label}</span>
                </div>
                <p className="text-slate-500 text-xs leading-relaxed pl-7">{gap.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bridge to solution */}
        <div className="text-center">
          <p className="text-slate-400 text-base mb-6 max-w-2xl mx-auto">
            VidShield AI replaces the entire manual moderation stack with a{' '}
            <span className="text-white font-semibold">fully autonomous, multi-modal AI pipeline</span>{' '}
            — faster, more accurate, and infinitely scalable.
          </p>
          <Link
            href="#features"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors shadow-lg shadow-blue-600/20"
          >
            See How We Solve This
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </section>
  );
}
