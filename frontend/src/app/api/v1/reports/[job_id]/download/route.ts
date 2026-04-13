import { NextResponse } from 'next/server';

// ── GET /api/v1/reports/:job_id/download ──────────────────────────────────────

export async function GET(
  _request: Request,
  { params }: { params: { job_id: string } }
) {
  // Mock: return a fake presigned URL
  return NextResponse.json({
    data: {
      download_url: `https://mock-s3.example.com/reports/${params.job_id}/report.pdf?token=mock`,
      expires_in_seconds: 3600,
      filename: 'report.pdf',
    },
  });
}
