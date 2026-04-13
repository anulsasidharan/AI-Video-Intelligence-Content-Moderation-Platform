'use client';

import Link from 'next/link';
import { ArrowRight, Play, Shield, Zap, Globe } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-slate-950 pt-16">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />

      {/* Animated grid */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            'linear-gradient(rgba(59,130,246,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.15) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-blue-600/10 border border-blue-500/30 rounded-full px-4 py-1.5 mb-8">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-blue-300 text-sm font-medium">
            Fully Autonomous · Zero Human Intervention
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-white leading-tight mb-6">
          AI-Powered{' '}
          <span className="bg-gradient-to-r from-blue-400 via-blue-300 to-indigo-400 bg-clip-text text-transparent">
            Video Intelligence
          </span>
          <br />
          & Content Moderation
        </h1>

        {/* Subheadline */}
        <p className="text-slate-300 text-lg sm:text-xl max-w-3xl mx-auto mb-10 leading-relaxed">
          VidShield AI analyzes live and recorded videos at scale — detecting violations,
          extracting insights, and moderating content autonomously using a 6-agent AI pipeline
          powered by GPT-4o and LangGraph.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base px-8 py-3.5 rounded-xl transition-all duration-200 shadow-lg shadow-blue-600/25 hover:shadow-blue-500/30"
          >
            Start for Free
            <ArrowRight size={18} />
          </Link>
          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold text-base px-8 py-3.5 rounded-xl transition-all duration-200"
          >
            <Play size={16} className="text-blue-400" />
            See How It Works
          </a>
        </div>

        {/* Trust Indicators */}
        <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 mb-20">
          {[
            { icon: Shield, label: 'GDPR Compliant' },
            { icon: Zap, label: 'Sub-2s Latency' },
            { icon: Globe, label: 'AWS Global Scale' },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-2 text-slate-400">
              <Icon size={16} className="text-blue-400" />
              <span className="text-sm font-medium">{label}</span>
            </div>
          ))}
        </div>

        {/* Dashboard Preview */}
        <div className="relative max-w-5xl mx-auto">
          <div className="bg-slate-900 border border-slate-700/60 rounded-2xl overflow-hidden shadow-2xl shadow-black/50">
            {/* Browser chrome */}
            <div className="flex items-center gap-2 px-4 py-3 bg-slate-800/80 border-b border-slate-700/60">
              <div className="w-3 h-3 rounded-full bg-red-400/70" />
              <div className="w-3 h-3 rounded-full bg-yellow-400/70" />
              <div className="w-3 h-3 rounded-full bg-green-400/70" />
              <div className="ml-4 flex-1 bg-slate-700/50 rounded-md h-6 flex items-center px-3">
                <span className="text-slate-400 text-xs">www.orionvexa.ca/dashboard</span>
              </div>
            </div>
            {/* Mock Dashboard */}
            <div className="p-6 bg-slate-900">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                {[
                  { label: 'Videos Processed', value: '24,891', color: 'text-blue-400' },
                  { label: 'Violations Detected', value: '1,247', color: 'text-red-400' },
                  { label: 'Accuracy Rate', value: '99.4%', color: 'text-green-400' },
                  { label: 'Avg Latency', value: '1.8s', color: 'text-yellow-400' },
                ].map((stat) => (
                  <div
                    key={stat.label}
                    className="bg-slate-800/70 border border-slate-700/40 rounded-xl p-4"
                  >
                    <div className={`text-2xl font-bold ${stat.color} mb-1`}>{stat.value}</div>
                    <div className="text-slate-400 text-xs">{stat.label}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2 bg-slate-800/50 border border-slate-700/40 rounded-xl p-4 h-32 flex flex-col justify-between">
                  <span className="text-slate-400 text-xs font-medium">Processing Activity</span>
                  <div className="flex items-end gap-1 h-16">
                    {[40, 65, 45, 80, 60, 90, 75, 55, 85, 70, 95, 60].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-blue-600/60 rounded-t"
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/40 rounded-xl p-4 h-32">
                  <span className="text-slate-400 text-xs font-medium">Violation Breakdown</span>
                  <div className="mt-3 space-y-2">
                    {[
                      { label: 'Violence', pct: '34%', color: 'bg-red-500' },
                      { label: 'Explicit', pct: '28%', color: 'bg-orange-500' },
                      { label: 'Hate Speech', pct: '22%', color: 'bg-yellow-500' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${item.color}`} />
                        <span className="text-slate-400 text-xs flex-1">{item.label}</span>
                        <span className="text-slate-300 text-xs font-medium">{item.pct}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* Glow under dashboard */}
          <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-3/4 h-20 bg-blue-600/20 blur-3xl rounded-full" />
        </div>
      </div>
    </section>
  );
}
