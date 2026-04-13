import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    data: {
      processed_count: 1284,
      violation_rate: 0.127,
      avg_latency_ms: 4320,
      p95_latency_ms: 9870,
      flagged_count: 98,
      rejected_count: 45,
      period_start: '2026-02-15T00:00:00Z',
      period_end: '2026-03-17T00:00:00Z',
    },
  });
}
