import { Play, BookOpen, Share2, Camera, ArrowRight } from 'lucide-react';
import Link from 'next/link';

const useCases = [
  {
    icon: Play,
    industry: 'Video Platforms',
    headline: 'YouTube-scale moderation without the manual overhead',
    description:
      'Automatically moderate user-generated content, detect policy violations before publishing, and maintain community standards at millions-of-video scale.',
    capabilities: [
      'Pre-publish content screening',
      'Re-upload detection via similarity search',
      'Age-restriction automation',
      'Violation appeal workflow',
    ],
    color: 'blue',
  },
  {
    icon: BookOpen,
    industry: 'EdTech Platforms',
    headline: 'Safe learning environments for every student',
    description:
      'Ensure all uploaded content meets educational standards. Automatically flag inappropriate material, enforce curriculum guidelines, and protect younger audiences.',
    capabilities: [
      'Age-appropriate content filtering',
      'Instructor content verification',
      'Safe-search transcript scanning',
      'COPPA-compliant processing',
    ],
    color: 'green',
  },
  {
    icon: Share2,
    industry: 'Social Media',
    headline: 'Real-time moderation for high-velocity feeds',
    description:
      'Moderate live streams and user posts in real time. Detect hate speech, graphic content, and misinformation the moment it appears — before it spreads.',
    capabilities: [
      'Live stream real-time analysis',
      'Trending content prioritization',
      'Multi-language OCR and transcript',
      'Coordinated inauthentic behavior',
    ],
    color: 'violet',
  },
  {
    icon: Camera,
    industry: 'Surveillance & Safety',
    headline: 'Intelligent video monitoring at any scale',
    description:
      'Analyze surveillance feeds for safety incidents, unauthorized activities, and anomalous behavior with configurable alert thresholds and instant notifications.',
    capabilities: [
      'Incident detection and alerting',
      'Scene classification',
      'Configurable sensitivity thresholds',
      'Webhook integration to SIEM',
    ],
    color: 'orange',
  },
];

const colorMap: Record<string, { icon: string; badge: string; border: string; glow: string }> = {
  blue: {
    icon: 'bg-blue-600/15 text-blue-400 border-blue-500/30',
    badge: 'bg-blue-600/15 text-blue-300',
    border: 'hover:border-blue-700/50',
    glow: 'group-hover:shadow-blue-900/20',
  },
  green: {
    icon: 'bg-green-600/15 text-green-400 border-green-500/30',
    badge: 'bg-green-600/15 text-green-300',
    border: 'hover:border-green-700/50',
    glow: 'group-hover:shadow-green-900/20',
  },
  violet: {
    icon: 'bg-violet-600/15 text-violet-400 border-violet-500/30',
    badge: 'bg-violet-600/15 text-violet-300',
    border: 'hover:border-violet-700/50',
    glow: 'group-hover:shadow-violet-900/20',
  },
  orange: {
    icon: 'bg-orange-600/15 text-orange-400 border-orange-500/30',
    badge: 'bg-orange-600/15 text-orange-300',
    border: 'hover:border-orange-700/50',
    glow: 'group-hover:shadow-orange-900/20',
  },
};

export function UseCases() {
  return (
    <section id="use-cases" className="bg-slate-900 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-4">
            <span className="text-blue-400 text-sm font-medium">Use Cases</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Built for every video-first industry
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            VidShield AI adapts to your domain with configurable policies, industry-specific categories, and flexible deployment options.
          </p>
        </div>

        {/* Use case cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {useCases.map((uc) => {
            const Icon = uc.icon;
            const colors = colorMap[uc.color];
            return (
              <div
                key={uc.industry}
                className={`group bg-slate-950/60 border border-slate-800/60 rounded-2xl p-7 transition-all duration-200 hover:shadow-xl ${colors.border} ${colors.glow}`}
              >
                <div className="flex items-center gap-3 mb-5">
                  <div className={`w-11 h-11 rounded-xl border flex items-center justify-center ${colors.icon}`}>
                    <Icon size={20} />
                  </div>
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full ${colors.badge}`}>
                    {uc.industry}
                  </span>
                </div>

                <h3 className="text-white font-bold text-xl mb-3 leading-tight">{uc.headline}</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-5">{uc.description}</p>

                <ul className="space-y-2 mb-5">
                  {uc.capabilities.map((cap) => (
                    <li key={cap} className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-slate-500 flex-shrink-0" />
                      <span className="text-slate-400 text-sm">{cap}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href="/register"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Get started
                  <ArrowRight size={14} />
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
