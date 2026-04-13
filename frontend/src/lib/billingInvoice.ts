import { getBrowserApiV1Root } from '@/lib/apiOrigin';

/**
 * Fetches the HTML invoice (not JSON-wrapped). Uses Bearer token from localStorage.
 */
export async function downloadBillingInvoice(paymentId: string): Promise<void> {
  if (typeof window === 'undefined') return;
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('You must be signed in to download an invoice.');
  }
  const url = `${getBrowserApiV1Root()}/billing/payments/${paymentId}/invoice`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let msg = `Could not download invoice (${res.status})`;
    try {
      const j = await res.json();
      if (j?.error?.message) msg = j.error.message;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  const blob = await res.blob();
  const cd = res.headers.get('Content-Disposition');
  const match = cd?.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? `invoice-${paymentId}.html`;
  const a = document.createElement('a');
  const href = URL.createObjectURL(blob);
  a.href = href;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}
