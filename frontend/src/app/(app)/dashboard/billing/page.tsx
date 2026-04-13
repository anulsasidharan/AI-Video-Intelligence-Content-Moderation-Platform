'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  ArrowUpRight,
  CreditCard,
  Download,
  FileText,
  Loader2,
  Receipt,
  Settings,
  Sparkles,
  Zap,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { downloadBillingInvoice } from '@/lib/billingInvoice';
import { apiClient } from '@/lib/api';
import { ROUTES } from '@/lib/constants';
import type {
  BillingPaymentList,
  PortalSessionResponse,
  SubscriptionView,
} from '@/types/billing';

function formatMoney(cents: number, currency: string) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency.toUpperCase() === 'XXX' ? 'USD' : currency.toUpperCase(),
  }).format(cents / 100);
}

const PAID_PLANS = ['starter', 'growth'];

function BillingBanners({
  onSuccess,
}: {
  onSuccess: () => void;
}) {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const success = searchParams.get('success');
    const canceled = searchParams.get('canceled');
    if (success === 'true') {
      // Sync subscription from Stripe immediately (webhooks can't reach localhost)
      apiClient
        .post<SubscriptionView>('/billing/sync')
        .then(() => {
          onSuccess();
          toast.success('Payment successful! Your plan has been updated.');
        })
        .catch(() => {
          toast.success('Payment successful! Refreshing your plan...');
          onSuccess();
        });
      router.replace('/dashboard/billing');
    } else if (canceled === 'true') {
      toast.info('Checkout canceled — no charge was made.');
      router.replace('/dashboard/billing');
    }
  }, [searchParams, router, onSuccess]);

  return null;
}

/** Upgrade banner shown to free-plan users */
function UpgradeBanner() {
  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
      <div className="rounded-lg bg-primary/10 p-3 shrink-0">
        <Sparkles className="h-6 w-6 text-primary" />
      </div>
      <div className="flex-1 space-y-1">
        <p className="font-semibold text-sm">You&apos;re on the Free plan</p>
        <p className="text-sm text-muted-foreground">
          Unlock GPT-4o vision analysis, live stream moderation, unlimited videos, and more.
          Paid plans start at <strong>$299/mo</strong> with a{' '}
          <strong>14-day free trial</strong> — no credit card required.
        </p>
      </div>
      <div className="flex gap-2 shrink-0">
        <Button asChild size="sm" className="gap-1.5">
          <Link href={ROUTES.pricing}>
            <Zap className="h-3.5 w-3.5" />
            See Plans
          </Link>
        </Button>
      </div>
    </div>
  );
}

export default function BillingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [portalLoading, setPortalLoading] = useState(false);
  const [syncAttempted, setSyncAttempted] = useState(false);

  const subQ = useQuery({
    queryKey: ['billing', 'subscription'],
    queryFn: () => apiClient.get<SubscriptionView>('/billing/subscription'),
  });

  const handleSyncSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['billing', 'subscription'] });
    queryClient.invalidateQueries({ queryKey: ['billing', 'payments'] });
  };

  const payQ = useQuery({
    queryKey: ['billing', 'payments'],
    queryFn: () => apiClient.get<BillingPaymentList>('/billing/payments?skip=0&limit=50'),
  });

  const planKey = subQ.data?.plan_key ?? 'free';
  const isOnPaidPlan = PAID_PLANS.includes(planKey);

  // Auto-backfill payment history from Stripe once when a paid user has no records
  // (handles the case where the webhook was configured after the initial payment)
  useEffect(() => {
    if (
      !syncAttempted &&
      isOnPaidPlan &&
      !payQ.isLoading &&
      !payQ.isFetching &&
      !payQ.isError &&
      payQ.data?.items.length === 0
    ) {
      setSyncAttempted(true);
      apiClient
        .post<{ synced: number }>('/billing/sync-payments')
        .then((res) => {
          if (res.synced > 0) {
            queryClient.invalidateQueries({ queryKey: ['billing', 'payments'] });
          }
        })
        .catch(() => {
          // Best-effort — silently skip if Stripe is unreachable
        });
    }
  }, [isOnPaidPlan, payQ.isLoading, payQ.isFetching, payQ.isError, payQ.data, syncAttempted, queryClient]);

  const onDownload = async (id: string) => {
    try {
      await downloadBillingInvoice(id);
      toast.success('Invoice download started');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Download failed');
    }
  };

  const handleManageBilling = async () => {
    setPortalLoading(true);
    try {
      const resp = await apiClient.post<PortalSessionResponse>('/billing/portal');
      window.location.href = resp.portal_url;
    } catch {
      toast.error('Could not open billing portal. Please try again.');
    } finally {
      setPortalLoading(false);
    }
  };

  const isOnFreePlan = !subQ.isLoading && planKey === 'free';

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Suspense fallback={null}>
        <BillingBanners onSuccess={handleSyncSuccess} />
      </Suspense>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Billing</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Subscription, payment history, and invoices for your organization.
        </p>
      </div>

      {/* Upgrade banner — free users only */}
      {isOnFreePlan && <UpgradeBanner />}

      {/* Current plan card */}
      <Card>
        <CardHeader className="flex flex-row items-start gap-3 space-y-0">
          <div className="rounded-lg border bg-muted/40 p-2">
            <CreditCard className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 space-y-1">
            <CardTitle className="text-base">Current plan</CardTitle>
            <CardDescription>Your VidShield subscription status</CardDescription>
          </div>
          {!subQ.isLoading && (
            <div className="flex gap-2">
              {isOnPaidPlan ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1.5"
                  onClick={handleManageBilling}
                  disabled={portalLoading}
                >
                  {portalLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Settings className="h-3.5 w-3.5" />
                  )}
                  Manage Billing
                </Button>
              ) : (
                <Button
                  size="sm"
                  className="gap-1.5"
                  onClick={() => router.push(ROUTES.pricing)}
                >
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  Upgrade Plan
                </Button>
              )}
            </div>
          )}
        </CardHeader>
        <CardContent>
          {subQ.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : subQ.isError ? (
            <p className="text-sm text-destructive">Could not load subscription.</p>
          ) : subQ.data ? (
            <dl className="grid gap-4 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Plan</dt>
                <dd className="mt-1 text-lg font-semibold capitalize">
                  {subQ.data.plan_key.replace(/_/g, ' ')}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Status</dt>
                <dd className="mt-1">
                  <Badge variant={subQ.data.status === 'active' ? 'default' : 'secondary'}>
                    {subQ.data.status}
                  </Badge>
                </dd>
              </div>
              {subQ.data.current_period_end && (
                <div className="sm:col-span-2">
                  <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Current period ends
                  </dt>
                  <dd className="mt-1 text-sm">
                    {format(new Date(subQ.data.current_period_end), 'PPP')}
                    {subQ.data.renews_label ? (
                      <span className="text-muted-foreground"> — {subQ.data.renews_label}</span>
                    ) : null}
                  </dd>
                </div>
              )}
            </dl>
          ) : null}
        </CardContent>
      </Card>

      {/* Payment history */}
      <Card>
        <CardHeader className="flex flex-row items-start gap-3 space-y-0">
          <div className="rounded-lg border bg-muted/40 p-2">
            <Receipt className="h-5 w-5 text-primary" />
          </div>
          <div className="space-y-1">
            <CardTitle className="text-base">Payment history</CardTitle>
            <CardDescription>Past charges and downloadable invoices (HTML — print or save as PDF)</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {payQ.isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : payQ.isError ? (
            <p className="text-sm text-destructive">Could not load payments.</p>
          ) : !payQ.data?.items.length ? (
            <div className="flex flex-col items-center justify-center gap-2 py-12 text-center text-sm text-muted-foreground">
              <FileText className="h-10 w-10 opacity-40" />
              <p>No payments yet. Invoices will appear here after your first charge.</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[100px] text-right">Invoice</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payQ.data.items.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="whitespace-nowrap text-sm">
                        {format(new Date(p.paid_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{p.invoice_number}</TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">
                        {p.description ?? '—'}
                      </TableCell>
                      <TableCell className="text-right text-sm font-medium">
                        {formatMoney(p.amount_cents, p.currency)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs capitalize">
                          {p.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="gap-1"
                          onClick={() => onDownload(p.id)}
                        >
                          <Download className="h-3.5 w-3.5" />
                          Download
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
