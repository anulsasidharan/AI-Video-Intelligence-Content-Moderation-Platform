import { NextResponse } from 'next/server';

export async function POST() {
  const videoId = 'vid-upload-' + Date.now();
  return NextResponse.json({
    data: {
      upload_url: `https://mock-s3.example.com/uploads/${videoId}`,
      video_id: videoId,
      expires_at: new Date(Date.now() + 3600_000).toISOString(),
    },
  });
}
