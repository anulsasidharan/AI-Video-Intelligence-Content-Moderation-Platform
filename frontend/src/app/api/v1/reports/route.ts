import { NextResponse } from 'next/server';

// ── Mock data ──────────────────────────────────────────────────────────────────

const MOCK_JOBS = [
  {
    id: 'rj-001',
    title: 'Weekly Moderation Summary',
    report_type: 'moderation_summary',
    status: 'ready',
    filters: { date_from: '2026-03-18', date_to: '2026-03-25' },
    columns: ['video_id', 'video_title', 'status', 'overall_confidence', 'violation_count', 'created_at'],
    orientation: 'portrait',
    s3_key: 'reports/rj-001/Weekly_Moderation_Summary.pdf',
    file_size_bytes: 148230,
    row_count: 84,
    error_message: null,
    celery_task_id: 'celery-abc-001',
    template_id: null,
    generated_by: 'user-admin-001',
    created_at: '2026-03-25T09:00:00Z',
    updated_at: '2026-03-25T09:01:42Z',
  },
  {
    id: 'rj-002',
    title: 'Monthly Video Activity Report',
    report_type: 'video_activity',
    status: 'ready',
    filters: { date_preset: 'last_30_days' },
    columns: null,
    orientation: 'landscape',
    s3_key: 'reports/rj-002/Monthly_Video_Activity_Report.pdf',
    file_size_bytes: 87450,
    row_count: 212,
    error_message: null,
    celery_task_id: 'celery-abc-002',
    template_id: null,
    generated_by: 'user-admin-001',
    created_at: '2026-03-24T14:30:00Z',
    updated_at: '2026-03-24T14:31:18Z',
  },
  {
    id: 'rj-003',
    title: 'Violation Breakdown — Q1 2026',
    report_type: 'violation_breakdown',
    status: 'generating',
    filters: { date_from: '2026-01-01', date_to: '2026-03-25' },
    columns: null,
    orientation: 'portrait',
    s3_key: null,
    file_size_bytes: null,
    row_count: null,
    error_message: null,
    celery_task_id: 'celery-abc-003',
    template_id: null,
    generated_by: 'user-admin-001',
    created_at: '2026-03-25T10:45:00Z',
    updated_at: '2026-03-25T10:45:10Z',
  },
  {
    id: 'rj-004',
    title: 'Agent Performance — March',
    report_type: 'agent_performance',
    status: 'failed',
    filters: { date_from: '2026-03-01', date_to: '2026-03-31' },
    columns: null,
    orientation: 'landscape',
    s3_key: null,
    file_size_bytes: null,
    row_count: null,
    error_message: 'Database timeout while querying agent_audit_logs.',
    celery_task_id: 'celery-abc-004',
    template_id: null,
    generated_by: 'user-admin-001',
    created_at: '2026-03-23T11:00:00Z',
    updated_at: '2026-03-23T11:00:45Z',
  },
];

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

// ── GET /api/v1/reports — list jobs ────────────────────────────────────────────

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') ?? '1');
  const pageSize = parseInt(searchParams.get('page_size') ?? '20');
  const statusFilter = searchParams.get('status');

  const filtered = statusFilter
    ? MOCK_JOBS.filter((j) => j.status === statusFilter)
    : MOCK_JOBS;

  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return NextResponse.json({
    data: { items, total: filtered.length, page, page_size: pageSize },
  });
}

// ── POST /api/v1/reports — queue generation ────────────────────────────────────

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const { title, report_type, filters, columns, orientation } = body as {
    title?: string;
    report_type?: string;
    filters?: Record<string, unknown>;
    columns?: string[] | null;
    orientation?: string;
  };

  if (!title || !report_type) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'title and report_type are required' } },
      { status: 400 }
    );
  }

  const newJob = {
    id: `rj-${Date.now()}`,
    title,
    report_type,
    status: 'generating',
    filters: filters ?? null,
    columns: columns ?? null,
    orientation: orientation ?? 'portrait',
    s3_key: null,
    file_size_bytes: null,
    row_count: null,
    error_message: null,
    celery_task_id: `mock-task-${Date.now()}`,
    template_id: null,
    generated_by: 'user-admin-001',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  return NextResponse.json({ data: newJob }, { status: 202 });
}
