import { NextResponse } from 'next/server';

const MOCK_VIDEOS = [
  {
    id: 'vid-001',
    filename: 'product-demo-v2.mp4',
    title: 'Product Demo v2',
    source: 'upload',
    status: 'completed',
    duration: 183,
    size: 48_234_567,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-15T10:04:00Z',
  },
  {
    id: 'vid-002',
    filename: 'user-generated-clip-49.mp4',
    title: 'User Clip #49',
    source: 'api',
    status: 'flagged',
    duration: 47,
    size: 9_123_456,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-16T08:22:00Z',
    updated_at: '2026-03-16T08:24:00Z',
  },
  {
    id: 'vid-003',
    filename: 'lecture-intro-ml.mp4',
    title: 'Intro to ML — Lecture 1',
    source: 'upload',
    status: 'processing',
    duration: null,
    size: 312_000_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-17T09:01:00Z',
    updated_at: '2026-03-17T09:01:30Z',
  },
  {
    id: 'vid-004',
    filename: 'onboarding-tour.webm',
    title: 'Onboarding Tour',
    source: 'upload',
    status: 'completed',
    duration: 92,
    size: 14_500_000,
    content_type: 'video/webm',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-14T14:30:00Z',
    updated_at: '2026-03-14T14:32:00Z',
  },
  {
    id: 'vid-005',
    filename: 'suspicious-content-7.mp4',
    title: null,
    source: 'api',
    status: 'flagged',
    duration: 28,
    size: 5_400_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-17T06:44:00Z',
    updated_at: '2026-03-17T06:46:00Z',
  },
  {
    id: 'vid-006',
    filename: 'quarterly-review.mp4',
    title: 'Q1 2026 Quarterly Review',
    source: 'upload',
    status: 'completed',
    duration: 3600,
    size: 890_000_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: null,
    created_at: '2026-03-10T11:00:00Z',
    updated_at: '2026-03-10T12:02:00Z',
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') ?? '1');
  const pageSize = parseInt(searchParams.get('page_size') ?? '20');
  const status = searchParams.get('status');

  const filtered = status ? MOCK_VIDEOS.filter((v) => v.status === status) : MOCK_VIDEOS;
  const start = (page - 1) * pageSize;
  const items = filtered.slice(start, start + pageSize);

  return NextResponse.json({
    data: { items, total: filtered.length, page, page_size: pageSize },
  });
}

export async function POST() {
  return NextResponse.json(
    { data: { video_id: 'vid-new-' + Date.now(), job_id: 'job-' + Date.now() } },
    { status: 201 }
  );
}
