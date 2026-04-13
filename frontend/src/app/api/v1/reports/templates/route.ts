import { NextResponse } from 'next/server';

const MOCK_TEMPLATES = [
  {
    id: 'rt-001',
    name: 'Weekly Moderation Digest',
    description: 'Standard weekly moderation summary for all videos.',
    report_type: 'moderation_summary',
    filters: { date_preset: 'last_7_days' },
    columns: ['video_id', 'video_title', 'status', 'overall_confidence', 'violation_count', 'created_at'],
    orientation: 'portrait',
    is_shared: true,
    owner_id: 'user-admin-001',
    created_at: '2026-03-01T08:00:00Z',
    updated_at: '2026-03-01T08:00:00Z',
  },
  {
    id: 'rt-002',
    name: 'Monthly Video Activity',
    description: 'All video uploads and status changes over the past 30 days.',
    report_type: 'video_activity',
    filters: { date_preset: 'last_30_days' },
    columns: null,
    orientation: 'landscape',
    is_shared: false,
    owner_id: 'user-admin-001',
    created_at: '2026-03-10T10:00:00Z',
    updated_at: '2026-03-10T10:00:00Z',
  },
];

export async function GET() {
  return NextResponse.json({ data: MOCK_TEMPLATES });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const { name, report_type } = body as { name?: string; report_type?: string };

  if (!name || !report_type) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'name and report_type are required' } },
      { status: 400 }
    );
  }

  const newTemplate = {
    id: `rt-${Date.now()}`,
    ...body,
    owner_id: 'user-admin-001',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  return NextResponse.json({ data: newTemplate }, { status: 201 });
}
