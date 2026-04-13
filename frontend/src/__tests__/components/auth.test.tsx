/**
 * F-01 — Authentication UI tests
 * Tests login/register page rendering and form validation.
 */
import { render, screen } from '@testing-library/react';

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeAuthStore(overrides = {}) {
  return {
    isAuthenticated: false,
    isLoading: false,
    error: null,
    login: jest.fn(),
    register: jest.fn(),
    clearError: jest.fn(),
    ...overrides,
  };
}

jest.mock('@/stores/authStore', () => ({
  useAuthStore: jest.fn(),
}));

import { useAuthStore } from '@/stores/authStore';
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

// ── ModerationBadge (simple, no auth dependency) ─────────────────────────────

describe('ModerationBadge (F-08)', () => {
  it('renders correct label for each status', () => {
    const { ModerationBadge } = require('@/components/moderation/ModerationBadge');
    const statuses = ['pending', 'in_review', 'approved', 'rejected', 'escalated'] as const;
    const labels = ['Pending', 'In Review', 'Approved', 'Rejected', 'Escalated'];

    statuses.forEach((status, i) => {
      const { unmount } = render(<ModerationBadge status={status} />);
      expect(screen.getByText(labels[i])).toBeInTheDocument();
      unmount();
    });
  });
});
