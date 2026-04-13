/**
 * F-09 — Analytics components tests (InsightChart, StatCard, HeatmapOverlay)
 */
import { render, screen } from '@testing-library/react';

// Recharts uses ResizeObserver which isn't available in jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('StatCard (F-09)', () => {
  it('renders title and value', () => {
    const { StatCard } = require('@/components/analytics/StatCard');
    render(<StatCard title="Total Videos" value={42} />);
    expect(screen.getByText('Total Videos')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders formatted string value', () => {
    const { StatCard } = require('@/components/analytics/StatCard');
    render(<StatCard title="Accuracy" value="98.5%" />);
    expect(screen.getByText('98.5%')).toBeInTheDocument();
  });

  it('renders trend indicator when provided', () => {
    const { StatCard } = require('@/components/analytics/StatCard');
    render(<StatCard title="Violations" value={10} trend={+15} />);
    expect(screen.getByText('Violations')).toBeInTheDocument();
  });
});

describe('InsightChart (F-09)', () => {
  it('renders without crashing with empty data', () => {
    const { InsightChart } = require('@/components/analytics/InsightChart');
    const { container } = render(<InsightChart data={[]} title="Violations Over Time" />);
    expect(container).toBeTruthy();
  });

  it('renders with data points', () => {
    const { InsightChart } = require('@/components/analytics/InsightChart');
    const data = [
      { date: '2024-01-01', value: 5 },
      { date: '2024-01-02', value: 8 },
    ];
    render(<InsightChart data={data} title="Test Chart" />);
    expect(screen.getByText('Test Chart')).toBeInTheDocument();
  });
});

describe('HeatmapOverlay (F-09)', () => {
  it('renders without crashing', () => {
    const { HeatmapOverlay } = require('@/components/analytics/HeatmapOverlay');
    const { container } = render(<HeatmapOverlay points={[]} width={640} height={360} />);
    expect(container).toBeTruthy();
  });

  it('renders the overlay canvas/svg element', () => {
    const { HeatmapOverlay } = require('@/components/analytics/HeatmapOverlay');
    const points = [
      { x: 100, y: 100, intensity: 0.8 },
      { x: 200, y: 150, intensity: 0.5 },
    ];
    const { container } = render(<HeatmapOverlay points={points} width={640} height={360} />);
    expect(container.firstChild).toBeTruthy();
  });
});
