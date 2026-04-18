import { NextResponse } from 'next/server';

// Verified-200 public domain test MP4s — distinct per video
const MOCK_VIDEOS: Record<string, object> = {
  'vid-001': {
    id: 'vid-001',
    filename: 'product-demo-v2.mp4',
    title: 'Product Demo v2',
    source: 'upload',
    status: 'completed',
    duration: 60,
    size: 48_234_567,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: 'https://www.w3schools.com/html/mov_bbb.mp4',
    job_id: 'job-demo-001',
    created_at: '2026-03-15T10:00:00Z',
    updated_at: '2026-03-15T10:04:00Z',
  },
  'vid-002': {
    id: 'vid-002',
    filename: 'user-generated-clip-49.mp4',
    title: 'User Clip #49',
    source: 'api',
    status: 'flagged',
    duration: 30,
    size: 9_123_456,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: 'https://www.w3schools.com/html/movie.mp4',
    job_id: 'job-demo-002',
    created_at: '2026-03-16T08:22:00Z',
    updated_at: '2026-03-16T08:24:00Z',
  },
  'vid-003': {
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
    job_id: 'job-demo-003',
    created_at: '2026-03-17T09:01:00Z',
    updated_at: '2026-03-17T09:01:30Z',
  },
  'vid-004': {
    id: 'vid-004',
    filename: 'onboarding-tour.mp4',
    title: 'Onboarding Tour',
    source: 'upload',
    status: 'completed',
    duration: 52,
    size: 14_500_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: 'https://media.w3.org/2010/05/sintel/trailer.mp4',
    job_id: 'job-demo-004',
    created_at: '2026-03-14T14:30:00Z',
    updated_at: '2026-03-14T14:32:00Z',
  },
  'vid-005': {
    id: 'vid-005',
    filename: 'suspicious-content-7.mp4',
    title: 'Suspicious Content #7',
    source: 'api',
    status: 'flagged',
    duration: 28,
    size: 5_400_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: 'https://media.w3.org/2010/05/video/movie_300.mp4',
    job_id: 'job-demo-005',
    created_at: '2026-03-17T06:44:00Z',
    updated_at: '2026-03-17T06:46:00Z',
  },
  'vid-006': {
    id: 'vid-006',
    filename: 'quarterly-review.mp4',
    title: 'Q1 2026 Quarterly Review',
    source: 'upload',
    status: 'completed',
    duration: 90,
    size: 890_000_000,
    content_type: 'video/mp4',
    thumbnail_url: null,
    playback_url: 'https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4',
    job_id: 'job-demo-006',
    created_at: '2026-03-10T11:00:00Z',
    updated_at: '2026-03-10T12:02:00Z',
  },
};

const FALLBACK = {
  filename: 'uploaded-video.mp4',
  title: 'Uploaded Video',
  source: 'upload',
  status: 'flagged',
  duration: 60,
  size: 48_234_567,
  content_type: 'video/mp4',
  thumbnail_url: null,
  playback_url: 'https://www.w3schools.com/html/mov_bbb.mp4',
  job_id: 'job-demo-new',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const video = MOCK_VIDEOS[params.id] ?? { ...FALLBACK, id: params.id };
  return NextResponse.json({ data: video });
}

export async function DELETE() {
  return NextResponse.json({ data: { message: 'Deleted' } });
}
