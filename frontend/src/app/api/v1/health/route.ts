import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ data: { status: 'ok', mode: 'mock', timestamp: new Date().toISOString() } });
}
