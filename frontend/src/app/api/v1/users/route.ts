import { NextResponse } from 'next/server';
import { MOCK_USER_STORE, saveStore } from '../auth/_store';

// Strip password before sending to client
function safeUser(u: (typeof MOCK_USER_STORE)[number]) {
  const { password: _pw, ...rest } = u;
  void _pw;
  return rest;
}

export async function GET() {
  return NextResponse.json({
    data: {
      items: MOCK_USER_STORE.map(safeUser),
      total: MOCK_USER_STORE.length,
    },
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({})) as Record<string, unknown>;
  const { name, email, password, role } = body as {
    name?: string; email?: string; password?: string; role?: string;
  };

  if (!name || !email || !password) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'Name, email, and password are required' } },
      { status: 400 }
    );
  }

  if (MOCK_USER_STORE.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    return NextResponse.json(
      { error: { code: 'EMAIL_TAKEN', message: 'A user with this email already exists' } },
      { status: 409 }
    );
  }

  const now = new Date().toISOString();
  const newUser = {
    id: 'user-' + Date.now(),
    email,
    password,
    name,
    role: (role === 'admin' ? 'admin' : 'operator') as 'admin' | 'operator',
    organization_id: 'org-vidshield-demo',
    created_at: now,
    updated_at: now,
  };

  MOCK_USER_STORE.push(newUser);
  saveStore();
  return NextResponse.json({ data: safeUser(newUser) }, { status: 201 });
}
