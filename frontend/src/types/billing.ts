export interface SubscriptionView {
  plan_key: string;
  status: string;
  current_period_end: string | null;
  renews_label: string | null;
}

export interface BillingPaymentItem {
  id: string;
  amount_cents: number;
  currency: string;
  status: string;
  paid_at: string;
  description: string | null;
  invoice_number: string;
}

export interface BillingPaymentList {
  items: BillingPaymentItem[];
  total: number;
}

export type RevenuePeriod = 'daily' | 'weekly' | 'monthly' | 'all';

export interface RevenueSeriesPoint {
  label: string;
  amount_cents: number;
}

export interface AdminRevenueResponse {
  period: RevenuePeriod;
  currency: string;
  total_cents: number;
  previous_period_total_cents: number | null;
  growth_percent: number | null;
  series: RevenueSeriesPoint[];
}

export interface SubscriberItem {
  email: string;
  name: string | null;
  role: string | null;
  user_id: string | null;
  source: 'account' | 'newsletter' | string;
  created_at: string;
}

export interface SubscriberListResponse {
  items: SubscriberItem[];
  total: number;
  page: number;
  page_size: number;
}

export type SubscriptionPlan = 'free' | 'starter' | 'growth' | 'enterprise';

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export interface PortalSessionResponse {
  portal_url: string;
}
