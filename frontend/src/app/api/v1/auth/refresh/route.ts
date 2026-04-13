import { NextResponse } from 'next/server';

export async function POST() {
  return NextResponse.json({
    data: {
      access_token: 'mock-access-token-refreshed-' + Date.now(),
      refresh_token: 'mock-refresh-token-refreshed-' + Date.now(),
      expires_in: 3600,
    },
  });
}
