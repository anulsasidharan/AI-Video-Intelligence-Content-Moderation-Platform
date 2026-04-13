/**
 * F-08 — ModerationBadge & ViolationCard component tests
 */
import { render, screen } from '@testing-library/react';
import { ModerationBadge } from '@/components/moderation/ModerationBadge';
import { ViolationCard } from '@/components/moderation/ViolationCard';
import type { ModerationStatus } from '@/types/moderation';
import type { Violation } from '@/types/moderation';

// ── ModerationBadge ───────────────────────────────────────────────────────────

describe('ModerationBadge (F-08)', () => {
  const cases: Array<[ModerationStatus, string]> = [
    ['pending', 'Pending'],
    ['in_review', 'In Review'],
    ['approved', 'Approved'],
    ['rejected', 'Rejected'],
    ['escalated', 'Escalated'],
  ];

  test.each(cases)('renders label "%s" → "%s"', (status, label) => {
    render(<ModerationBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('accepts an optional className prop', () => {
    const { container } = render(
      <ModerationBadge status="approved" className="custom-class" />
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });
});

// ── ViolationCard ─────────────────────────────────────────────────────────────

const baseViolation: Violation = {
  id: 'v-001',
  category: 'violence',
  confidence: 0.92,
  timestamp_seconds: 15.5,
};

describe('ViolationCard (F-08)', () => {
  it('renders violation category', () => {
    render(<ViolationCard violation={baseViolation} />);
    expect(screen.getByText(/violence/i)).toBeInTheDocument();
  });

  it('renders confidence as a percentage', () => {
    render(<ViolationCard violation={baseViolation} />);
    expect(screen.getByText(/92/)).toBeInTheDocument();
  });

  it('renders timestamp when provided', () => {
    render(<ViolationCard violation={baseViolation} />);
    expect(screen.getByText(/15/)).toBeInTheDocument();
  });

  it('renders without timestamp when omitted', () => {
    const { id, category, confidence } = baseViolation;
    render(<ViolationCard violation={{ id, category, confidence }} />);
    expect(screen.getByText(/violence/i)).toBeInTheDocument();
  });
});
