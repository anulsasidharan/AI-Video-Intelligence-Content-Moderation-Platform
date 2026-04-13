import { NextResponse } from 'next/server';

// In-memory store — persists for the lifetime of the dev server process
const MOCK_STREAMS = [
  {
    id: 'stream-001',
    title: 'Live Classroom — CS101',
    status: 'active',
    alert_count: 0,
    created_at: '2026-03-17T08:00:00Z',
  },
  {
    id: 'stream-002',
    title: 'Public Event Feed',
    status: 'active',
    alert_count: 2,
    created_at: '2026-03-17T09:30:00Z',
  },
  {
    id: 'stream-003',
    title: 'Archived Stream — Mar 16',
    status: 'stopped',
    alert_count: 1,
    created_at: '2026-03-16T14:00:00Z',
  },
];

export async function GET() {
  return NextResponse.json({
    data: { items: MOCK_STREAMS, total: MOCK_STREAMS.length, page: 1, page_size: 20 },
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({})) as Record<string, unknown>;

  const newStream = {
    id: 'stream-' + Date.now(),
    title: (body.title as string) || 'Untitled Stream',
    stream_url: (body.stream_url as string) || '',
    description: (body.description as string) || '',
    status: 'active' as const,
    alert_count: 0,
    created_at: new Date().toISOString(),
  };

  MOCK_STREAMS.unshift(newStream);

  return NextResponse.json({ data: newStream }, { status: 201 });
}
