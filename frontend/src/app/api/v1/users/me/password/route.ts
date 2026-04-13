import { NextResponse } from 'next/server';
import { MOCK_USER_STORE, saveStore } from '../../../auth/_store';

function getUserIdFromHeader(req: Request): string | null {
  const auth = req.headers.get('authorization') ?? '';
  // mock token format: "mock-{userId}-{timestamp}"
  const match = auth.replace('Bearer ', '').match(/^mock-(.+)-\d+$/);
  return match ? match[1] : null;
}

export async function PATCH(request: Request) {
  const userId = getUserIdFromHeader(request);
  if (!userId) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Not authenticated' } },
      { status: 401 }
    );
  }

  const idx = MOCK_USER_STORE.findIndex((u) => u.id === userId);
  if (idx === -1) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'User not found' } },
      { status: 404 }
    );
  }

  const body = await request.json().catch(() => ({})) as Record<string, unknown>;
  const { current_password, new_password } = body as {
    current_password?: string;
    new_password?: string;
  };

  if (!current_password || !new_password) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'current_password and new_password are required' } },
      { status: 400 }
    );
  }

  const user = MOCK_USER_STORE[idx];
  if (user.password !== current_password) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Current password is incorrect' } },
      { status: 401 }
    );
  }

  if (new_password.length < 8) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'New password must be at least 8 characters' } },
      { status: 400 }
    );
  }

  user.password = new_password;
  user.updated_at = new Date().toISOString();
  saveStore();

  const { password: _pw, ...safeUser } = user;
  void _pw;
  return NextResponse.json({ data: safeUser });
}
