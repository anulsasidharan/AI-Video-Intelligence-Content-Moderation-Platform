import { NextResponse } from 'next/server';

export async function GET(_req: Request, { params }: { params: { video_id: string } }) {
  return NextResponse.json({
    data: {
      id: 'q-mock-' + params.video_id,
      video_id: params.video_id,
      status: 'pending',
      priority: 2,
      report: {
        violations: [
          {
            id: 'v-mock-1',
            category: 'violence',
            timestamp_seconds: 12,
            confidence: 0.91,
            snippet: 'Detected physical altercation in frame sequence 24–31',
            frame_url: null,
          },
        ],
        recommended_action: 'reject',
        summary: 'High-confidence violation detected during AI analysis.',
        processed_at: new Date().toISOString(),
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  });
}
