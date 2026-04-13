import { type NextRequest, NextResponse } from 'next/server';

// Server-side proxy: use the internal backend URL (API_UPSTREAM_URL) so this
// route handler works both in Docker Compose (http://backend:8000) and in
// development (http://localhost:8000). Never use API_BASE_URL here — that is
// an empty string in production (same-origin browser calls) and would cause
// fetch() to fail with a relative URL in Node.js.
const SERVER_API_BASE =
  process.env.API_UPSTREAM_URL?.replace(/\/+$/, '') ?? 'http://localhost:8000';

async function proxyRequest(request: NextRequest): Promise<NextResponse> {
  const url = new URL(request.url);
  const targetUrl = `${SERVER_API_BASE}${url.pathname}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete('host');

  try {
    const body =
      request.method !== 'GET' && request.method !== 'HEAD'
        ? await request.arrayBuffer()
        : undefined;

    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
      // @ts-expect-error — node fetch duplex
      duplex: 'half',
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete('transfer-encoding');

    const responseBody = await response.arrayBuffer();

    return new NextResponse(responseBody, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (err) {
    console.error('[proxy] upstream error:', err);
    return NextResponse.json(
      { error: { code: 'UPSTREAM_ERROR', message: 'Unable to reach backend service' } },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyRequest(request);
}

export async function POST(request: NextRequest) {
  return proxyRequest(request);
}

export async function PATCH(request: NextRequest) {
  return proxyRequest(request);
}

export async function PUT(request: NextRequest) {
  return proxyRequest(request);
}

export async function DELETE(request: NextRequest) {
  return proxyRequest(request);
}
