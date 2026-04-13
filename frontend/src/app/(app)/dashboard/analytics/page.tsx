import { redirect } from 'next/navigation';

// Analytics has been merged into the Overview page.
export default function AnalyticsRedirect() {
  redirect('/dashboard');
}
