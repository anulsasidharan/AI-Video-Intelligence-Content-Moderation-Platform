/**
 * F-10 — Live stream components tests (StreamMonitor, AlertBanner)
 */
import { render, screen, act } from '@testing-library/react';
import { StreamMonitor, type StreamSummary } from '@/components/live/StreamMonitor';
import { AlertBanner } from '@/components/live/AlertBanner';
import { useModerationStore } from '@/stores/moderationStore';

// ── StreamMonitor ─────────────────────────────────────────────────────────────
// StreamMonitor renders: {stream.title ?? stream.id.slice(0, 12)}…
// The Unicode ellipsis (…) is appended directly in JSX, so use regex matchers.

const baseStream: StreamSummary = {
  id: 'stream-001',
  title: 'Main Camera Feed',
  status: 'active',
  created_at: new Date().toISOString(),
};

describe('StreamMonitor (F-10)', () => {
  it('renders stream title (may include trailing ellipsis)', () => {
    render(<StreamMonitor streams={[baseStream]} />);
    expect(screen.getByText(/Main Camera Feed/)).toBeInTheDocument();
  });

  it('renders ACTIVE status badge', () => {
    render(<StreamMonitor streams={[baseStream]} />);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders STOPPED status badge', () => {
    render(<StreamMonitor streams={[{ ...baseStream, status: 'stopped' }]} />);
    expect(screen.getByText('STOPPED')).toBeInTheDocument();
  });

  it('renders empty message when no streams', () => {
    render(<StreamMonitor streams={[]} />);
    expect(screen.getByText(/no active streams/i)).toBeInTheDocument();
  });

  it('renders loading skeletons when isLoading', () => {
    const { container } = render(<StreamMonitor streams={[]} isLoading />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders Stop stream button for active stream when onStop provided', () => {
    const onStop = jest.fn();
    render(<StreamMonitor streams={[baseStream]} onStop={onStop} />);
    expect(screen.getByLabelText('Stop stream')).toBeInTheDocument();
  });

  it('calls onStop with stream id when stop button clicked', () => {
    const onStop = jest.fn();
    render(<StreamMonitor streams={[baseStream]} onStop={onStop} />);
    screen.getByLabelText('Stop stream').click();
    expect(onStop).toHaveBeenCalledWith('stream-001');
  });

  it('renders multiple streams', () => {
    const streams: StreamSummary[] = [
      { ...baseStream, id: 's1', title: 'Camera 1' },
      { ...baseStream, id: 's2', title: 'Camera 2' },
    ];
    render(<StreamMonitor streams={streams} />);
    expect(screen.getByText(/Camera 1/)).toBeInTheDocument();
    expect(screen.getByText(/Camera 2/)).toBeInTheDocument();
  });
});

// ── AlertBanner ───────────────────────────────────────────────────────────────
// AlertBanner reads from useModerationStore — seed the store directly.

beforeEach(() => {
  useModerationStore.setState({ liveAlerts: [] });
});

describe('AlertBanner (F-10)', () => {
  it('renders nothing when there are no undismissed alerts', () => {
    const { container } = render(<AlertBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('renders alert category when an alert is present', () => {
    act(() => {
      useModerationStore.getState().addLiveAlert({
        id: 'a1',
        category: 'violence',
        confidence: 0.92,
        timestamp: new Date().toISOString(),
      });
    });
    render(<AlertBanner />);
    expect(screen.getByText(/violence/i)).toBeInTheDocument();
  });

  it('hides alert after dismissing it', () => {
    act(() => {
      useModerationStore.getState().addLiveAlert({
        id: 'a2',
        category: 'nudity',
        confidence: 0.88,
        timestamp: new Date().toISOString(),
      });
    });
    render(<AlertBanner />);
    const dismissBtn = screen.getByLabelText('Dismiss alert');
    act(() => { dismissBtn.click(); });
    expect(screen.queryByText(/nudity/i)).not.toBeInTheDocument();
  });

  it('renders at most 3 alerts visible', () => {
    act(() => {
      for (let i = 0; i < 5; i++) {
        useModerationStore.getState().addLiveAlert({
          id: `a${i}`,
          category: 'spam',
          confidence: 0.7,
          timestamp: new Date().toISOString(),
        });
      }
    });
    render(<AlertBanner />);
    // 5 alerts, only 3 shown + "+2 more alerts" message
    expect(screen.getByText(/\+2 more/)).toBeInTheDocument();
  });
});
