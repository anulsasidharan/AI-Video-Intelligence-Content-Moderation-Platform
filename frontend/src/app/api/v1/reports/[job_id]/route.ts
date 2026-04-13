import { NextResponse } from 'next/server';

// ── GET /api/v1/reports/:job_id ────────────────────────────────────────────────

export async function GET(
  _request: Request,
  { params }: { params: { job_id: string } }
) {
  // In production this would proxy to the FastAPI backend.
  // Mock: return a "ready" job stub.
  return NextResponse.json({
    data: {
      id: params.job_id,
      title: 'Mock Report',
      report_type: 'moderation_summary',
      status: 'ready',
      filters: null,
      columns: null,
      orientation: 'portrait',
      s3_key: `reports/${params.job_id}/Mock_Report.pdf`,
      file_size_bytes: 102400,
      row_count: 50,
      error_message: null,
      celery_task_id: 'mock-task',
      template_id: null,
      generated_by: 'user-admin-001',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  });
}

// ── DELETE /api/v1/reports/:job_id ─────────────────────────────────────────────

export async function DELETE(
  _request: Request,
  { params }: { params: { job_id: string } }
) {
  return new NextResponse(null, { status: 204 });
}
