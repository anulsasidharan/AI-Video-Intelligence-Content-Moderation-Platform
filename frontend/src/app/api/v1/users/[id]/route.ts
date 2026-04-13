import { NextResponse } from 'next/server';
import { MOCK_USER_STORE, saveStore } from '../../auth/_store';

interface RouteContext {
  params: { id: string };
}

export async function PATCH(request: Request, { params }: RouteContext) {
  const idx = MOCK_USER_STORE.findIndex((u) => u.id === params.id);
  if (idx === -1) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'User not found' } },
      { status: 404 }
    );
  }

  const body = await request.json().catch(() => ({})) as Record<string, unknown>;
  const { name, role, password } = body as {
    name?: string; role?: string; password?: string;
  };

  const user = MOCK_USER_STORE[idx];
  if (name) user.name = name;
  if (role === 'admin' || role === 'operator') user.role = role;
  if (password && password.length >= 8) user.password = password;
  user.updated_at = new Date().toISOString();

  saveStore();
  const { password: _pw, ...safeUser } = user;
  void _pw;
  return NextResponse.json({ data: safeUser });
}

export async function DELETE(_req: Request, { params }: RouteContext) {
  const idx = MOCK_USER_STORE.findIndex((u) => u.id === params.id);
  if (idx === -1) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'User not found' } },
      { status: 404 }
    );
  }

  MOCK_USER_STORE.splice(idx, 1);
  saveStore();
  return NextResponse.json({ data: { message: 'User deleted' } });
}
