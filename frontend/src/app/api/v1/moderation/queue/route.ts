import { NextResponse } from 'next/server';

const MOCK_QUEUE = [
  {
    id: 'q-001',
    video_id: 'vid-002',
    status: 'pending',
    priority: 1,
    report: {
      violations: [
        { id: 'v-001', category: 'violence', timestamp_seconds: 12, confidence: 0.91, snippet: 'Detected physical altercation in frame sequence 24–31' },
        { id: 'v-002', category: 'hate_symbols', timestamp_seconds: 38, confidence: 0.76, snippet: 'Symbol detected in background' },
      ],
      recommended_action: 'reject',
      summary: 'Video contains high-confidence violence and potential hate symbols.',
      processed_at: '2026-03-16T08:24:00Z',
    },
    created_at: '2026-03-16T08:22:00Z',
    updated_at: '2026-03-16T08:24:00Z',
  },
  {
    id: 'q-002',
    video_id: 'vid-005',
    status: 'in_review',
    priority: 2,
    report: {
      violations: [
        { id: 'v-003', category: 'nudity', timestamp_seconds: 8, confidence: 0.83, snippet: null },
      ],
      recommended_action: 'escalate',
      summary: 'Potential nudity detected. Escalated for human review.',
      processed_at: '2026-03-17T06:46:00Z',
    },
    created_at: '2026-03-17T06:44:00Z',
    updated_at: '2026-03-17T06:46:00Z',
  },
  {
    id: 'q-003',
    video_id: 'vid-001',
    status: 'approved',
    priority: 3,
    report: {
      violations: [],
      recommended_action: 'approve',
      summary: 'No violations detected. Content is safe.',
      processed_at: '2026-03-15T10:04:00Z',
    },
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-15T10:05:00Z',
  },
  {
    id: 'q-004',
    video_id: 'vid-004',
    status: 'approved',
    priority: 3,
    report: {
      violations: [],
      recommended_action: 'approve',
      summary: 'Clean content.',
      processed_at: '2026-03-14T14:32:00Z',
    },
    created_at: '2026-03-14T14:30:00Z',
    updated_at: '2026-03-14T14:33:00Z',
  },
  {
    id: 'q-005',
    video_id: 'vid-006',
    status: 'escalated',
    priority: 1,
    report: {
      violations: [
        { id: 'v-004', category: 'misinformation', timestamp_seconds: 240, confidence: 0.68, snippet: 'Potentially misleading health claims detected in transcript.' },
      ],
      recommended_action: 'escalate',
      summary: 'Possible misinformation. Requires expert review.',
      processed_at: '2026-03-10T12:02:00Z',
    },
    created_at: '2026-03-10T11:00:00Z',
    updated_at: '2026-03-10T12:05:00Z',
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') ?? '1');
  const pageSize = parseInt(searchParams.get('page_size') ?? '20');
  const status = searchParams.get('status');

  const filtered = status ? MOCK_QUEUE.filter((q) => q.status === status) : MOCK_QUEUE;
  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return NextResponse.json({
    data: { items, total: filtered.length, page, page_size: pageSize },
  });
}
