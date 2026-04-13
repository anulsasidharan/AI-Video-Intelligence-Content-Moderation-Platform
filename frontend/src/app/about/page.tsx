import Link from 'next/link';
import { Shield, Target, Eye, Zap, Users, Globe, Award, CheckCircle } from 'lucide-react';
import { Navbar } from '@/components/landing/Navbar';
import { LandingFooter } from '@/components/landing/LandingFooter';

const values = [
  {
    icon: Shield,
    title: 'Safety First',
    description:
      'We believe every platform deserves enterprise-grade content moderation without the enterprise overhead. Safety is not a feature — it is the foundation.',
  },
  {
    icon: Zap,
    title: 'Fully Autonomous',
    description:
      'Our AI pipeline operates end-to-end without human intervention for standard decisions. Speed and scale that manual moderation can never match.',
  },
  {
    icon: Eye,
    title: 'Transparent AI',
    description:
      'Every moderation decision is explainable. Audit trails, confidence scores, and agent reasoning are exposed so operators always understand why.',
  },
  {
    icon: Globe,
    title: 'Built for Scale',
    description:
      'From indie platforms to global enterprises, VidShield scales horizontally across video, live streams, and multi-tenant environments.',
  },
];

const milestones = [
  { year: '2023', event: 'Founded by a team of AI and video infrastructure engineers' },
  { year: 'Q1 2024', event: 'Launched beta with 3 design partners — 50 M+ videos processed' },
  { year: 'Q3 2024', event: 'Released LangGraph multi-agent pipeline and real-time live-stream moderation' },
  { year: 'Q1 2025', event: 'SOC 2 Type II certified; expanded to 12 enterprise customers' },
  { year: '2025', event: 'Processing 500 M+ videos monthly across 30 countries' },
];

const team = [
  { name: 'Sudhanshu', role: 'Co-Founder & CEO', bio: 'Former ML lead at a top-tier streaming platform. 12 years in video AI.' },
  { name: 'Anu L Sasidharan', role: 'Co-Founder & CTO', bio: 'Systems architect with deep expertise in distributed video processing.' },
  { name: 'Abhrajit Pal', role: 'Head of AI Research', bio: 'PhD in Computer Vision. Pioneered the multi-agent moderation graph.' },
  { name: 'Manish Mishra', role: 'VP Engineering', bio: 'Scaled infrastructure to 1 B+ requests/day at previous roles.' },
  { name: 'Naveen Srikakolapu', role: 'Lead Backend Engineer', bio: 'FastAPI and distributed systems specialist. Open-source contributor.' },
  { name: 'Prodip Sarkar', role: 'Lead Frontend Engineer', bio: 'Crafts the dashboards and real-time UIs that make data actionable.' },
  { name: 'Rajiv Ranjan', role: 'DevOps & Infrastructure', bio: 'AWS certified architect. Built the ECS Fargate + Terraform pipeline.' },
  { name: 'Ruthvik Kumar', role: 'Product & Integrations', bio: 'Bridges enterprise requirements with platform capabilities.' },
];

const stats = [
  { value: '500M+', label: 'Videos processed monthly' },
  { value: '99.7%', label: 'Moderation accuracy' },
  { value: '<2s', label: 'Average decision latency' },
  { value: '30+', label: 'Countries served' },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
            <Award size={14} className="text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">About VidShield AI</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-6 leading-tight">
            Making the internet{' '}
            <span className="text-blue-400">safer</span>, one video at a time
          </h1>
          <p className="text-slate-400 text-lg leading-relaxed max-w-2xl mx-auto">
            VidShield AI is an enterprise-grade AI Video Intelligence &amp; Content Moderation Platform
            built for platforms that refuse to compromise on safety or speed. We combine cutting-edge
            computer vision, large language models, and a fully autonomous multi-agent pipeline to
            protect your users at scale.
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-slate-800/60 bg-slate-900/30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {stats.map((s) => (
              <div key={s.label}>
                <div className="text-3xl font-bold text-white mb-1">{s.value}</div>
                <div className="text-slate-500 text-sm">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Target size={18} className="text-blue-400" />
                <span className="text-blue-400 text-sm font-semibold uppercase tracking-wider">Our Mission</span>
              </div>
              <h2 className="text-3xl font-bold mb-4">
                Autonomous moderation that never sleeps
              </h2>
              <p className="text-slate-400 leading-relaxed mb-4">
                Content platforms face an impossible challenge: the volume of user-generated video
                grows faster than any human moderation team can keep pace with. Harmful content
                reaches audiences within seconds. Reputations — and lives — are affected.
              </p>
              <p className="text-slate-400 leading-relaxed">
                Our mission is to give every platform — from an indie EdTech startup to a global
                social network — the same moderation capabilities that only the largest tech
                companies have historically been able to afford.
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Eye size={18} className="text-purple-400" />
                <span className="text-purple-400 text-sm font-semibold uppercase tracking-wider">Our Vision</span>
              </div>
              <h2 className="text-3xl font-bold mb-4">
                A world where AI makes platforms inherently safe
              </h2>
              <p className="text-slate-400 leading-relaxed mb-4">
                We envision a future where content moderation is invisible infrastructure —
                like a CDN or a firewall — that every platform runs automatically, at zero
                marginal cost per video analyzed.
              </p>
              <p className="text-slate-400 leading-relaxed">
                Zero human-in-the-loop for standard decisions. Full explainability for edge cases.
                Continuous model improvement from every platform we serve.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">What we stand for</h2>
            <p className="text-slate-400">The principles that guide every decision we make</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-6">
            {values.map((v) => (
              <div
                key={v.title}
                className="bg-slate-900 border border-slate-800/60 rounded-2xl p-6 hover:border-slate-700/60 transition-colors"
              >
                <div className="w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-center mb-4">
                  <v.icon size={18} className="text-blue-400" />
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">{v.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{v.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">Our journey</h2>
            <p className="text-slate-400">From idea to processing half a billion videos a month</p>
          </div>
          <div className="relative">
            <div className="absolute left-6 top-0 bottom-0 w-px bg-slate-800" />
            <div className="space-y-8">
              {milestones.map((m) => (
                <div key={m.year} className="flex gap-6 items-start">
                  <div className="relative flex-shrink-0">
                    <div className="w-12 h-12 bg-slate-900 border-2 border-blue-500/40 rounded-full flex items-center justify-center">
                      <CheckCircle size={16} className="text-blue-400" />
                    </div>
                  </div>
                  <div className="pt-2">
                    <div className="text-blue-400 text-sm font-semibold mb-1">{m.year}</div>
                    <div className="text-slate-300 text-sm">{m.event}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-2 mb-3">
              <Users size={18} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-semibold uppercase tracking-wider">The Team</span>
            </div>
            <h2 className="text-3xl font-bold mb-3">Built by practitioners</h2>
            <p className="text-slate-400">
              Engineers and researchers who have lived the content moderation problem firsthand
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {team.map((member) => (
              <div
                key={member.name}
                className="bg-slate-900 border border-slate-800/60 rounded-2xl p-5 hover:border-slate-700/60 transition-colors"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-blue-500/20 rounded-full flex items-center justify-center mb-3">
                  <span className="text-white font-bold text-lg">
                    {member.name.charAt(0)}
                  </span>
                </div>
                <div className="font-semibold text-white text-sm mb-0.5">{member.name}</div>
                <div className="text-blue-400 text-xs mb-2">{member.role}</div>
                <p className="text-slate-500 text-xs leading-relaxed">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to protect your platform?</h2>
          <p className="text-slate-400 mb-8">
            Join the platforms that trust VidShield AI to keep their communities safe.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Get started free
            </Link>
            <Link
              href="/contact"
              className="inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Talk to sales
            </Link>
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
}
