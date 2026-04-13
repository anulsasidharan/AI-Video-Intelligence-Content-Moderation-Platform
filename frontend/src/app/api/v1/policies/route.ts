import { NextResponse } from 'next/server';

const MOCK_POLICIES = [
  {
    id: 'pol-001',
    name: 'Strict Violence Policy',
    description: 'Zero tolerance for violent content. Auto-rejects on high confidence.',
    categories: ['violence', 'hate_symbols'],
    rules: [
      { category: 'violence', threshold: 0.7, action: 'auto_reject' },
      { category: 'hate_symbols', threshold: 0.6, action: 'escalate' },
    ],
    actions: ['auto_reject', 'notify'],
    is_active: true,
    created_at: '2026-01-10T09:00:00Z',
    updated_at: '2026-03-01T12:00:00Z',
  },
  {
    id: 'pol-002',
    name: 'Adult Content Policy',
    description: 'Flags and escalates nudity for human review.',
    categories: ['nudity', 'drugs'],
    rules: [
      { category: 'nudity', threshold: 0.75, action: 'escalate' },
      { category: 'drugs', threshold: 0.65, action: 'auto_flag' },
    ],
    actions: ['auto_flag', 'escalate'],
    is_active: true,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-02-20T14:00:00Z',
  },
  {
    id: 'pol-003',
    name: 'Misinformation Guard',
    description: 'Detects potential misinformation in transcripts.',
    categories: ['misinformation', 'spam'],
    rules: [
      { category: 'misinformation', threshold: 0.8, action: 'escalate' },
      { category: 'spam', threshold: 0.9, action: 'auto_flag' },
    ],
    actions: ['escalate', 'notify'],
    is_active: false,
    created_at: '2026-02-01T08:00:00Z',
    updated_at: '2026-02-01T08:00:00Z',
  },
];

export async function GET() {
  return NextResponse.json({
    data: { items: MOCK_POLICIES, total: MOCK_POLICIES.length, page: 1, page_size: 20 },
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const newPolicy = {
    id: 'pol-' + Date.now(),
    ...body,
    is_active: body.is_active ?? true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  return NextResponse.json({ data: newPolicy }, { status: 201 });
}
