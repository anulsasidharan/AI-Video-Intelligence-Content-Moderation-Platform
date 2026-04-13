import { NextResponse } from 'next/server';

// ── POST /api/v1/reports/preview ───────────────────────────────────────────────

const MOCK_PREVIEW: Record<string, { columns: string[]; rows: object[]; summary: object }> = {
  moderation_summary: {
    columns: ['video_id', 'video_title', 'status', 'overall_confidence', 'violation_count', 'created_at'],
    rows: [
      { video_id: 'vid-001', video_title: 'Product Demo v2', status: 'approved', overall_confidence: 0.97, violation_count: 0, created_at: '2026-03-25T08:00:00Z' },
      { video_id: 'vid-002', video_title: 'Live Event Highlights', status: 'rejected', overall_confidence: 0.89, violation_count: 3, created_at: '2026-03-24T15:30:00Z' },
      { video_id: 'vid-003', video_title: 'Tutorial: Getting Started', status: 'approved', overall_confidence: 0.99, violation_count: 0, created_at: '2026-03-24T12:00:00Z' },
      { video_id: 'vid-004', video_title: 'User Generated #482', status: 'flagged', overall_confidence: 0.72, violation_count: 1, created_at: '2026-03-23T09:15:00Z' },
      { video_id: 'vid-005', video_title: 'Marketing Campaign Q1', status: 'escalated', overall_confidence: 0.65, violation_count: 2, created_at: '2026-03-22T11:00:00Z' },
    ],
    summary: { total: 84, by_status: { approved: 61, rejected: 8, flagged: 9, escalated: 6 }, avg_confidence: 0.87 },
  },
  video_activity: {
    columns: ['video_id', 'title', 'status', 'source', 'duration_seconds', 'file_size_bytes', 'owner_email', 'created_at'],
    rows: [
      { video_id: 'vid-001', title: 'Product Demo v2', status: 'ready', source: 'upload', duration_seconds: 142, file_size_bytes: 52428800, owner_email: 'alice@acme.com', created_at: '2026-03-25T08:00:00Z' },
      { video_id: 'vid-002', title: 'Live Event Highlights', status: 'ready', source: 'live', duration_seconds: 3620, file_size_bytes: 1073741824, owner_email: 'bob@acme.com', created_at: '2026-03-24T15:30:00Z' },
      { video_id: 'vid-003', title: 'Tutorial: Getting Started', status: 'ready', source: 'upload', duration_seconds: 780, file_size_bytes: 209715200, owner_email: 'alice@acme.com', created_at: '2026-03-24T12:00:00Z' },
    ],
    summary: { total: 212, total_size_bytes: 2147483648, total_duration_seconds: 18423.5, by_status: { ready: 198, failed: 7, processing: 5, pending: 2 } },
  },
  user_activity: {
    columns: ['user_id', 'email', 'name', 'role', 'is_active', 'created_at'],
    rows: [
      { user_id: 'u-001', email: 'alice@acme.com', name: 'Alice Chen', role: 'admin', is_active: true, created_at: '2026-01-15T00:00:00Z' },
      { user_id: 'u-002', email: 'bob@acme.com', name: 'Bob Smith', role: 'operator', is_active: true, created_at: '2026-02-01T00:00:00Z' },
      { user_id: 'u-003', email: 'carol@acme.com', name: 'Carol Wang', role: 'api_consumer', is_active: false, created_at: '2026-02-20T00:00:00Z' },
    ],
    summary: { total: 24, by_role: { admin: 3, operator: 8, api_consumer: 13 } },
  },
  agent_performance: {
    columns: ['trace_id', 'agent_name', 'status', 'duration_ms', 'input_tokens', 'output_tokens', 'error_message', 'created_at'],
    rows: [
      { trace_id: 'tr-001', agent_name: 'content_analyzer', status: 'success', duration_ms: 2340, input_tokens: 1200, output_tokens: 420, error_message: '—', created_at: '2026-03-25T09:00:00Z' },
      { trace_id: 'tr-001', agent_name: 'safety_checker', status: 'success', duration_ms: 1870, input_tokens: 980, output_tokens: 310, error_message: '—', created_at: '2026-03-25T09:00:02Z' },
      { trace_id: 'tr-002', agent_name: 'scene_classifier', status: 'failed', duration_ms: 450, input_tokens: 640, output_tokens: 0, error_message: 'LLM timeout after 30s', created_at: '2026-03-24T14:10:00Z' },
    ],
    summary: { total: 1284 },
  },
  violation_breakdown: {
    columns: ['event_date', 'category', 'count', 'avg_confidence', 'video_count'],
    rows: [
      { event_date: '2026-03-25', category: 'violence', count: 12, avg_confidence: 0.88, video_count: 10 },
      { event_date: '2026-03-25', category: 'nudity', count: 5, avg_confidence: 0.91, video_count: 5 },
      { event_date: '2026-03-24', category: 'hate_speech', count: 3, avg_confidence: 0.77, video_count: 3 },
      { event_date: '2026-03-24', category: 'misinformation', count: 7, avg_confidence: 0.69, video_count: 6 },
    ],
    summary: { total_violations: 98, unique_date_category_pairs: 28 },
  },
};

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const { report_type, page = 1, page_size = 50 } = body as {
    report_type?: string;
    page?: number;
    page_size?: number;
  };

  const mock = MOCK_PREVIEW[report_type ?? 'moderation_summary'] ?? MOCK_PREVIEW.moderation_summary;
  const start = (page - 1) * page_size;
  const rows = mock.rows.slice(start, start + page_size);

  return NextResponse.json({
    data: {
      columns: mock.columns,
      rows,
      total: mock.rows.length,
      page,
      page_size,
      summary: mock.summary,
    },
  });
}
