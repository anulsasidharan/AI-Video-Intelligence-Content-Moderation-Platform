import { NextResponse } from 'next/server';
import { MOCK_USER_STORE, saveStore } from '../_store';

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const { email, password, name, role } = body as {
    email?: string;
    password?: string;
    name?: string;
    role?: string;
  };

  if (!email || !password || !name) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'Name, email, and password are required' } },
      { status: 400 }
    );
  }

  const exists = MOCK_USER_STORE.some(
    (u) => u.email.toLowerCase() === email.toLowerCase()
  );

  if (exists) {
    return NextResponse.json(
      { error: { code: 'EMAIL_TAKEN', message: 'An account with this email already exists' } },
      { status: 409 }
    );
  }

  const validRole = role === 'admin' || role === 'operator' ? role : 'operator';
  const now = new Date().toISOString();

  const newUser = {
    id: 'user-' + Date.now(),
    email,
    password,
    name,
    role: validRole as 'admin' | 'operator',
    organization_id: 'org-vidshield-demo',
    created_at: now,
    updated_at: now,
  };

  MOCK_USER_STORE.push(newUser);
  saveStore();

  return NextResponse.json(
    { data: { message: 'Account created successfully. Please sign in.' } },
    { status: 201 }
  );
}
