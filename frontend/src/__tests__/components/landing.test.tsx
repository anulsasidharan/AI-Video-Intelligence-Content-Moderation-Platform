import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock next/navigation (not needed for landing page but included for safety)
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  redirect: jest.fn(),
}));

// Mock next/link
jest.mock('next/link', () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = 'MockLink';
  return MockLink;
});

// ---------------------------------------------------------------------------
// Navbar
// ---------------------------------------------------------------------------
import { Navbar } from '@/components/landing/Navbar';

describe('Navbar', () => {
  it('renders the VidShield AI brand name', () => {
    render(<Navbar />);
    expect(screen.getByText('VidShield')).toBeInTheDocument();
  });

  it('renders all primary nav links', () => {
    render(<Navbar />);
    expect(screen.getAllByText('Features').length).toBeGreaterThan(0);
    expect(screen.getAllByText('How It Works').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Pricing').length).toBeGreaterThan(0);
  });

  it('renders sign in and get started links', () => {
    render(<Navbar />);
    expect(screen.getAllByText('Sign In').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Get Started Free').length).toBeGreaterThan(0);
  });

  it('toggles mobile menu when hamburger button is clicked', () => {
    render(<Navbar />);
    const menuButton = screen.getByLabelText('Toggle mobile menu');
    fireEvent.click(menuButton);
    // After opening, the button should render the X (close) icon
    expect(menuButton).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------
import { Stats } from '@/components/landing/Stats';

describe('Stats', () => {
  it('renders key metric values', () => {
    render(<Stats />);
    expect(screen.getByText('99.9%')).toBeInTheDocument();
    expect(screen.getByText('<2s')).toBeInTheDocument();
    expect(screen.getByText('99.4%')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('renders all stat labels', () => {
    render(<Stats />);
    expect(screen.getByText('Platform Uptime')).toBeInTheDocument();
    expect(screen.getByText('Moderation Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Specialized AI Agents')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Features
// ---------------------------------------------------------------------------
import { Features } from '@/components/landing/Features';

describe('Features', () => {
  it('renders the section heading', () => {
    render(<Features />);
    expect(
      screen.getByText('Everything you need to moderate video at scale')
    ).toBeInTheDocument();
  });

  it('renders the Multi-Agent AI Pipeline feature', () => {
    render(<Features />);
    expect(screen.getByText('Multi-Agent AI Pipeline')).toBeInTheDocument();
  });

  it('renders the Webhooks & REST API feature', () => {
    render(<Features />);
    expect(screen.getByText('Webhooks & REST API')).toBeInTheDocument();
  });

  it('renders 12 feature cards', () => {
    render(<Features />);
    // Each feature card has a unique title
    expect(screen.getByText('RBAC & Audit Logging')).toBeInTheDocument();
    expect(screen.getByText('Similarity Search (RAG)')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// HowItWorks
// ---------------------------------------------------------------------------
import { HowItWorks } from '@/components/landing/HowItWorks';

describe('HowItWorks', () => {
  it('renders the section heading', () => {
    render(<HowItWorks />);
    expect(
      screen.getByText('From upload to moderation report in seconds')
    ).toBeInTheDocument();
  });

  it('renders all three steps', () => {
    render(<HowItWorks />);
    expect(screen.getByText('Ingest Video')).toBeInTheDocument();
    expect(screen.getByText('AI Pipeline Analyzes')).toBeInTheDocument();
    expect(screen.getByText('Receive Moderation Report')).toBeInTheDocument();
  });

  it('renders step numbers', () => {
    render(<HowItWorks />);
    expect(screen.getByText('01')).toBeInTheDocument();
    expect(screen.getByText('02')).toBeInTheDocument();
    expect(screen.getByText('03')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AgentArchitecture
// ---------------------------------------------------------------------------
import { AgentArchitecture } from '@/components/landing/AgentArchitecture';

describe('AgentArchitecture', () => {
  it('renders the section heading', () => {
    render(<AgentArchitecture />);
    expect(
      screen.getByText('6 specialist AI agents working in concert')
    ).toBeInTheDocument();
  });

  it('renders all 6 agent cards', () => {
    render(<AgentArchitecture />);
    expect(screen.getByText('Orchestrator Agent')).toBeInTheDocument();
    expect(screen.getByText('Content Analyzer')).toBeInTheDocument();
    expect(screen.getByText('Safety Checker')).toBeInTheDocument();
    expect(screen.getByText('Metadata Extractor')).toBeInTheDocument();
    expect(screen.getByText('Scene Classifier')).toBeInTheDocument();
    expect(screen.getByText('Report Generator')).toBeInTheDocument();
  });

  it('renders technology tags', () => {
    render(<AgentArchitecture />);
    expect(screen.getByText('LangGraph')).toBeInTheDocument();
    expect(screen.getByText('GPT-4o Vision')).toBeInTheDocument();
    expect(screen.getByText('OpenAI Whisper')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// UseCases
// ---------------------------------------------------------------------------
import { UseCases } from '@/components/landing/UseCases';

describe('UseCases', () => {
  it('renders the section heading', () => {
    render(<UseCases />);
    expect(screen.getByText('Built for every video-first industry')).toBeInTheDocument();
  });

  it('renders all four industry cards', () => {
    render(<UseCases />);
    expect(screen.getByText('Video Platforms')).toBeInTheDocument();
    expect(screen.getByText('EdTech Platforms')).toBeInTheDocument();
    expect(screen.getByText('Social Media')).toBeInTheDocument();
    expect(screen.getByText('Surveillance & Safety')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Integrations
// ---------------------------------------------------------------------------
import { Integrations } from '@/components/landing/Integrations';

describe('Integrations', () => {
  it('renders the section heading', () => {
    render(<Integrations />);
    expect(screen.getByText('Integrate in minutes, not weeks')).toBeInTheDocument();
  });

  it('renders REST API section', () => {
    render(<Integrations />);
    expect(screen.getByText('REST API')).toBeInTheDocument();
  });

  it('renders webhook events', () => {
    render(<Integrations />);
    expect(screen.getByText('moderation.completed')).toBeInTheDocument();
    expect(screen.getByText('violation.detected')).toBeInTheDocument();
    expect(screen.getByText('stream.status')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Security
// ---------------------------------------------------------------------------
import { Security } from '@/components/landing/Security';

describe('Security', () => {
  it('renders the section heading', () => {
    render(<Security />);
    expect(
      screen.getByText('Enterprise-grade security, built in — not bolted on')
    ).toBeInTheDocument();
  });

  it('renders key security features', () => {
    render(<Security />);
    expect(screen.getByText('JWT & API Key Auth')).toBeInTheDocument();
    expect(screen.getByText('PII Detection & Masking')).toBeInTheDocument();
    expect(screen.getByText('GDPR-Aware Design')).toBeInTheDocument();
  });

  it('renders compliance badges', () => {
    render(<Security />);
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText('HTTPS/TLS')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Pricing
// ---------------------------------------------------------------------------
import { Pricing } from '@/components/landing/Pricing';

describe('Pricing', () => {
  it('renders the section heading', () => {
    render(<Pricing />);
    expect(screen.getByText('Simple, transparent pricing')).toBeInTheDocument();
  });

  it('renders all three pricing tiers', () => {
    render(<Pricing />);
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Growth')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  it('renders plan prices', () => {
    render(<Pricing />);
    expect(screen.getByText('$299')).toBeInTheDocument();
    expect(screen.getByText('$999')).toBeInTheDocument();
    expect(screen.getByText('Custom')).toBeInTheDocument();
  });

  it('renders CTA buttons', () => {
    render(<Pricing />);
    expect(screen.getAllByText('Start Free Trial').length).toBe(2);
    expect(screen.getByText('Contact Sales')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// FAQ
// ---------------------------------------------------------------------------
import { FAQ } from '@/components/landing/FAQ';

describe('FAQ', () => {
  it('renders the section heading', () => {
    render(<FAQ />);
    expect(screen.getByText('Frequently asked questions')).toBeInTheDocument();
  });

  it('renders FAQ questions', () => {
    render(<FAQ />);
    expect(
      screen.getByText('How long does it take to process a video?')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Does VidShield AI support live stream moderation?')
    ).toBeInTheDocument();
  });

  it('expands an answer when a question is clicked', () => {
    render(<FAQ />);
    const firstQuestion = screen.getByText('How long does it take to process a video?');
    fireEvent.click(firstQuestion);
    expect(
      screen.getByText(/Average end-to-end processing time is under 2 seconds/)
    ).toBeInTheDocument();
  });

  it('collapses an answer when the same question is clicked again', () => {
    render(<FAQ />);
    const firstQuestion = screen.getByText('How long does it take to process a video?');
    fireEvent.click(firstQuestion);
    fireEvent.click(firstQuestion);
    expect(
      screen.queryByText(/Average end-to-end processing time is under 2 seconds/)
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// CTASection
// ---------------------------------------------------------------------------
import { CTASection } from '@/components/landing/CTASection';

describe('CTASection', () => {
  it('renders the CTA heading', () => {
    render(<CTASection />);
    expect(
      screen.getByText('Ready to automate your')
    ).toBeInTheDocument();
  });

  it('renders the trial CTA button', () => {
    render(<CTASection />);
    expect(screen.getByText('Start Free 14-Day Trial')).toBeInTheDocument();
  });

  it('renders the contact sales button', () => {
    render(<CTASection />);
    expect(screen.getByText('Contact Sales')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// LandingFooter
// ---------------------------------------------------------------------------
import { LandingFooter } from '@/components/landing/LandingFooter';

describe('LandingFooter', () => {
  it('renders the brand name', () => {
    render(<LandingFooter />);
    expect(screen.getAllByText('VidShield').length).toBeGreaterThan(0);
  });

  it('renders footer link categories', () => {
    render(<LandingFooter />);
    expect(screen.getByText('Company')).toBeInTheDocument();
    expect(screen.getByText('Developers')).toBeInTheDocument();
  });

  it('renders copyright text', () => {
    render(<LandingFooter />);
    expect(screen.getByText(/VidShield AI\. All rights reserved\./)).toBeInTheDocument();
  });

  it('renders system status indicator', () => {
    render(<LandingFooter />);
    expect(screen.getByText('All systems operational')).toBeInTheDocument();
  });

  it('renders all 8 team member names', () => {
    render(<LandingFooter />);
    expect(screen.getByText('Sudhanshu')).toBeInTheDocument();
    expect(screen.getByText('Anu L Sasidharan')).toBeInTheDocument();
    expect(screen.getByText('Abhrajit Pal')).toBeInTheDocument();
    expect(screen.getByText('Manish Mishra')).toBeInTheDocument();
    expect(screen.getByText('Naveen Srikakolapu')).toBeInTheDocument();
    expect(screen.getByText('Prodip Sarkar')).toBeInTheDocument();
    expect(screen.getByText('Rajiv Ranjan')).toBeInTheDocument();
    expect(screen.getByText('Ruthvik Kumar')).toBeInTheDocument();
  });

  it('renders legal links', () => {
    render(<LandingFooter />);
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
    expect(screen.getByText('Terms & Conditions')).toBeInTheDocument();
    expect(screen.getByText('Cookie Policy')).toBeInTheDocument();
  });

  it('renders newsletter subscription form', () => {
    render(<LandingFooter />);
    expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
    expect(screen.getByText('Subscribe')).toBeInTheDocument();
  });

  it('shows success message after subscribing', async () => {
    const prevFetch = globalThis.fetch;
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { ok: true, message: "Thanks — you're on the list." } }),
    });
    globalThis.fetch = mockFetch as unknown as typeof fetch;

    render(<LandingFooter />);
    const emailInput = screen.getByPlaceholderText('your@email.com');
    const subscribeBtn = screen.getByText('Subscribe');
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(subscribeBtn);

    await waitFor(() => {
      expect(screen.getByText(/You're subscribed/)).toBeInTheDocument();
    });
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/newsletter$/),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com' }),
      })
    );
    globalThis.fetch = prevFetch;
  });
});

// ---------------------------------------------------------------------------
// ProblemStatement
// ---------------------------------------------------------------------------
import { ProblemStatement } from '@/components/landing/ProblemStatement';

describe('ProblemStatement', () => {
  it('renders the problem section heading', () => {
    render(<ProblemStatement />);
    expect(screen.getByText(/Video content moderation is broken/)).toBeInTheDocument();
  });

  it('renders all 4 pain point stats', () => {
    render(<ProblemStatement />);
    expect(screen.getByText('72 hours')).toBeInTheDocument();
    expect(screen.getByText('$1.4M+')).toBeInTheDocument();
    expect(screen.getByText('23%')).toBeInTheDocument();
    expect(screen.getByText('500%')).toBeInTheDocument();
  });

  it('renders pain point labels', () => {
    render(<ProblemStatement />);
    expect(screen.getByText('Average manual review backlog')).toBeInTheDocument();
    expect(screen.getByText('False-positive rate in rule-based filters')).toBeInTheDocument();
  });

  it('renders the why existing solutions fail section', () => {
    render(<ProblemStatement />);
    expect(screen.getByText('Why existing solutions fall short')).toBeInTheDocument();
    expect(screen.getByText('Slow')).toBeInTheDocument();
    expect(screen.getByText('Expensive')).toBeInTheDocument();
    expect(screen.getByText('Inaccurate')).toBeInTheDocument();
    expect(screen.getByText('Rigid')).toBeInTheDocument();
  });

  it('renders the bridge CTA', () => {
    render(<ProblemStatement />);
    expect(screen.getByText('See How We Solve This')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// SocialProof
// ---------------------------------------------------------------------------
import { SocialProof } from '@/components/landing/SocialProof';

describe('SocialProof', () => {
  it('renders the section heading', () => {
    render(<SocialProof />);
    expect(screen.getByText('Real impact, measurable results')).toBeInTheDocument();
  });

  it('renders all 4 impact metrics', () => {
    render(<SocialProof />);
    expect(screen.getByText('87%')).toBeInTheDocument();
    expect(screen.getByText('1.8s')).toBeInTheDocument();
    expect(screen.getByText('99.4%')).toBeInTheDocument();
    expect(screen.getByText('23x')).toBeInTheDocument();
  });

  it('renders 3 testimonial cards', () => {
    render(<SocialProof />);
    expect(screen.getByText('Head of Trust & Safety')).toBeInTheDocument();
    expect(screen.getByText('VP of Product')).toBeInTheDocument();
    expect(screen.getByText('Engineering Lead')).toBeInTheDocument();
  });

  it('renders industry trust section', () => {
    render(<SocialProof />);
    expect(screen.getByText('Trusted across industries')).toBeInTheDocument();
    expect(screen.getByText('Video Platforms')).toBeInTheDocument();
    expect(screen.getByText('EdTech Companies')).toBeInTheDocument();
  });
});
