const APP_ENV = process.env.NEXT_PUBLIC_APP_ENV ?? 'development';
/** Treat like production for API base defaults (avoid http localhost in cloud deploys). */
const IS_PROD_LIKE = APP_ENV === 'production' || APP_ENV === 'staging';

function isLocalhostUrl(url: string): boolean {
  try {
    const u = new URL(url);
    return u.hostname === 'localhost' || u.hostname === '127.0.0.1';
  } catch {
    return /localhost|127\.0\.0\.1/.test(url);
  }
}

/**
 * Browser API base (no /api/v1 suffix).
 * - "" = same-origin `/api/v1/...` (required behind ALB path routing or Next rewrites).
 * - Never use localhost in production builds: browsers would call the end-user's machine.
 */
function resolveApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  // In production/staging always use same-origin ("") so browser API calls
  // inherit the page protocol (https) and can never trigger Mixed Content.
  // The ALB routes /api/v1/* to the backend on the same domain.
  if (IS_PROD_LIKE) return '';
  if (raw === '') return '';
  if (raw !== undefined && raw !== '') return raw;
  return 'http://localhost:8000';
}

function resolveWsUrl(): string {
  const raw = process.env.NEXT_PUBLIC_WS_URL;
  // Same-origin for WebSocket in production — avoids ws:// Mixed Content.
  if (IS_PROD_LIKE) return '';
  if (raw === '') return '';
  if (raw !== undefined && raw !== '') return raw;
  return 'http://localhost:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();
export const WS_URL = resolveWsUrl();

export const API_V1 = '/api/v1';

export const ROUTES = {
  home: '/',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password',
  dashboard: '/dashboard',
  analytics: '/dashboard',
  settings: '/dashboard/settings',
  profile: '/dashboard/profile',
  userManagement: '/dashboard/users',
  auditTrail: '/dashboard/audit',
  videos: '/videos',
  videoUpload: '/videos/upload',
  videoDetail: (id: string) => `/videos/${id}`,
  moderation: '/moderation',
  moderationQueue: '/moderation/queue',
  moderationPolicies: '/moderation/policies',
  live: '/live',
  liveStream: (id: string) => `/live/${id}`,
  apiKeys: '/dashboard/api-keys',
  billing: '/dashboard/billing',
  pricing: '/dashboard/pricing',
  adminRevenue: '/dashboard/revenue',
  adminSubscribers: '/dashboard/subscribers',
  reports: '/reports',
  reportBuilder: '/reports/builder',
  supportTickets: '/dashboard/support-tickets',
  about: '/about',
  contact: '/contact',
  support: '/support',
  docsApiReference: '/docs/api-reference',
  docsWebhooks: '/docs/webhooks',
  docsSdk: '/docs/sdk',
  docsIntegrations: '/docs/integrations',
  developerPortal: '/docs/developer-portal',
} as const;

export const PAGE_SIZE_DEFAULT = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export const ACCEPTED_VIDEO_TYPES = [
  'video/mp4',
  'video/webm',
  'video/ogg',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-matroska',
];

export const MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024 * 1024; // 5 GB

export const VIOLATION_CATEGORY_LABELS: Record<string, string> = {
  violence: 'Violence',
  nudity: 'Nudity',
  drugs: 'Drugs',
  hate_symbols: 'Hate Symbols',
  spam: 'Spam',
  misinformation: 'Misinformation',
  other: 'Other',
};

export const MODERATION_STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  in_review: 'In Review',
  approved: 'Approved',
  rejected: 'Rejected',
  escalated: 'Escalated',
  flagged: 'Flagged',
};

export const VIDEO_STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  flagged: 'Flagged',
  ready: 'Ready',
  failed: 'Failed',
  deleted: 'Deleted',
};
