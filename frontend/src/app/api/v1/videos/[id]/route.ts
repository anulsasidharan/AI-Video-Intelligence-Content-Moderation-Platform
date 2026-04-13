import { NextResponse } from 'next/server';

const MOCK_VIDEO = {
  id: 'vid-001',
  filename: 'product-demo-v2.mp4',
  title: 'Product Demo v2',
  source: 'upload',
  status: 'flagged',
  duration: 183,
  size: 48_234_567,
  content_type: 'video/mp4',
  thumbnail_url: null,
  playback_url: 'https://www.w3schools.com/html/mov_bbb.mp4',
  job_id: 'job-demo-001',
  created_at: '2026-03-15T10:00:00Z',
  updated_at: '2026-03-15T10:04:00Z',
};

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  return NextResponse.json({ data: { ...MOCK_VIDEO, id: params.id } });
}

export async function DELETE() {
  return NextResponse.json({ data: { message: 'Deleted' } });
}
