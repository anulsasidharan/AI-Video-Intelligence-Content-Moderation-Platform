import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Hero } from '@/components/landing/Hero';
import { ProblemStatement } from '@/components/landing/ProblemStatement';
import { Stats } from '@/components/landing/Stats';
import { Features } from '@/components/landing/Features';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { AgentArchitecture } from '@/components/landing/AgentArchitecture';
import { UseCases } from '@/components/landing/UseCases';
import { SocialProof } from '@/components/landing/SocialProof';
import { Integrations } from '@/components/landing/Integrations';
import { Security } from '@/components/landing/Security';
import { Pricing } from '@/components/landing/Pricing';
import { FAQ } from '@/components/landing/FAQ';
import { CTASection } from '@/components/landing/CTASection';
import { LandingFooter } from '@/components/landing/LandingFooter';

export const metadata: Metadata = {
  title: 'VidShield AI — AI Video Intelligence & Content Moderation Platform',
  description:
    'Enterprise-grade AI video moderation platform. Autonomous content safety analysis for live and recorded video using GPT-4o, LangGraph multi-agent pipeline, and policy-driven decisions.',
  keywords: [
    'video moderation',
    'AI content moderation',
    'video intelligence',
    'content safety',
    'GPT-4o video analysis',
    'live stream moderation',
    'LangGraph agents',
    'automated moderation',
  ],
  openGraph: {
    title: 'VidShield AI — AI Video Intelligence & Content Moderation',
    description:
      'Fully autonomous AI video moderation. 6-agent pipeline, real-time live stream analysis, policy-driven decisions — zero human intervention required.',
    type: 'website',
  },
};

export default function LandingPage() {
  return (
    <div className="bg-slate-950 text-white antialiased">
      <Navbar />
      <main>
        {/* 1. Hero — immediate value prop */}
        <Hero />
        {/* 2. Problem Statement — why this matters (CRITICAL) */}
        <ProblemStatement />
        {/* 3. Stats — credibility */}
        <Stats />
        {/* 4. Features — what we offer */}
        <Features />
        {/* 5. How It Works — the process */}
        <HowItWorks />
        {/* 6. AI Agents — technical depth */}
        <AgentArchitecture />
        {/* 7. Use Cases — industry fit */}
        <UseCases />
        {/* 8. Social Proof — trust signals */}
        <SocialProof />
        {/* 9. Integrations — developer confidence */}
        <Integrations />
        {/* 10. Security — compliance assurance */}
        <Security />
        {/* 11. Pricing — conversion */}
        <Pricing />
        {/* 12. FAQ — objection handling */}
        <FAQ />
        {/* 13. Final CTA — conversion */}
        <CTASection />
      </main>
      <LandingFooter />
    </div>
  );
}
