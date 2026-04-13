/** @type {import('next').NextConfig} */
// Server-side rewrites only: where the Next.js server forwards /api/v1/*. Use API_UPSTREAM_URL when
// NEXT_PUBLIC_API_URL is "" (browser uses same-origin /api/v1) but the backend has a different URL
// inside Docker/ECS (e.g. http://backend:8000 or internal ALB DNS).
// API_UPSTREAM_URL must be an internal/direct backend URL (e.g. http://backend:8000).
// Do NOT fall back to NEXT_PUBLIC_API_URL here: that is the public-facing domain and
// would create an ALB→Next.js→ALB infinite loop in production.
const rawUpstream = process.env.API_UPSTREAM_URL || 'http://localhost:8000';
const apiUpstreamUrl = String(rawUpstream).replace(/\/+$/, '');

const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  images: {
    remotePatterns: [
      // Local development / LocalStack
      { protocol: 'http', hostname: 'localhost', port: '**' },
      { protocol: 'http', hostname: '127.0.0.1', port: '**' },
      // AWS S3 — virtual-hosted style: {bucket}.s3.{region}.amazonaws.com
      { protocol: 'https', hostname: '**.amazonaws.com' },
      // Custom S3 bucket domain via env var
      ...(process.env.S3_BUCKET_DOMAIN
        ? [{ protocol: 'https', hostname: process.env.S3_BUCKET_DOMAIN }]
        : []),
    ],
  },
  async rewrites() {
    // In mock mode the API client points at localhost:3000 (this server).
    // Skip the rewrite entirely to avoid an infinite redirect loop and let
    // the mock route handlers under src/app/api/v1/ respond directly.
    if (process.env.NEXT_PUBLIC_MOCK_API === 'true') return [];
    // In production, API_UPSTREAM_URL must be set to an internal backend URL.
    // If it is not set (e.g. first deploy or local dev without it), skip the
    // rewrite so the ALB handles /api/* routing directly. Applying a rewrite
    // that points back at the public domain creates an infinite loop.
    if (!process.env.API_UPSTREAM_URL && process.env.NEXT_PUBLIC_APP_ENV === 'production') return [];
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiUpstreamUrl}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
      // Allow same-machine cross-port requests in dev/mock mode
      ...(process.env.NEXT_PUBLIC_MOCK_API === 'true'
        ? [
            {
              source: '/api/:path*',
              headers: [
                { key: 'Access-Control-Allow-Origin', value: '*' },
                { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PATCH,PUT,DELETE,OPTIONS' },
                { key: 'Access-Control-Allow-Headers', value: 'Content-Type,Authorization' },
              ],
            },
          ]
        : []),
    ];
  },
};

module.exports = nextConfig;
