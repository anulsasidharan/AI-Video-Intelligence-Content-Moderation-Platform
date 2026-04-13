import { NextResponse } from 'next/server';

// ── POST /api/v1/reports/generate ─────────────────────────────────────────────

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

  const jobId = `rj-${Date.now()}`;
  const newJob = {
    id: jobId,
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
