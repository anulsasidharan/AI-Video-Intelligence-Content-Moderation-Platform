import { API_BASE_URL, API_V1 } from '@/lib/constants';

/**
 * Resolves the API v1 root (`/api/v1` or `https://host/api/v1`) for the current environment.
 * In the browser on an HTTPS page, upgrades `http://` API bases to `https://` so XHR/fetch
 * are not blocked by mixed-content policy.
 */
export function getBrowserApiV1Root(): string {
  if (typeof window === 'undefined') {
    return `${API_BASE_URL}${API_V1}`;
  }
  let base = API_BASE_URL;
  if (window.location.protocol === 'https:' && base.startsWith('http://')) {
    try {
      base = new URL(base).origin.replace('http:', 'https:');
    } catch {
      /* keep base */
    }
  }
  if (!base) return API_V1;
  return `${base.replace(/\/$/, '')}${API_V1}`;
}
