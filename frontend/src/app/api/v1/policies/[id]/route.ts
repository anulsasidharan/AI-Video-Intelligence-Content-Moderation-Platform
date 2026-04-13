import { NextResponse } from 'next/server';

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  return NextResponse.json({ data: { id: params.id, name: 'Mock Policy' } });
}

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  const body = await request.json().catch(() => ({}));
  return NextResponse.json({ data: { id: params.id, ...body, updated_at: new Date().toISOString() } });
}

export async function DELETE() {
  return NextResponse.json({ data: { message: 'Deleted' } });
}
