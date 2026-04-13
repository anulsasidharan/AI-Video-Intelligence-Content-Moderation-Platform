'use client';

import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { ArrowDownRight, ArrowUpRight, Loader2, Minus, TrendingUp } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { ROUTES } from '@/lib/constants';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import type { AdminRevenueResponse, RevenuePeriod } from '@/types/billing';

const PERIODS: { value: RevenuePeriod; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'all', label: 'All time' },
];

function formatMoney(cents: number, currency: string) {
  const c = currency.toUpperCase() === 'XXX' ? 'USD' : currency.toUpperCase();
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: c }).format(cents / 100);
}

export default function AdminRevenuePage() {
  const router = useRouter();
  const { isAdmin, user } = useAuth();
  const [period, setPeriod] = useState<RevenuePeriod>('monthly');

  useEffect(() => {
    if (user && !isAdmin) {
      router.replace(ROUTES.dashboard);
    }
  }, [isAdmin, user, router]);

  const q = useQuery({
    queryKey: ['admin', 'billing', 'revenue', period],
    queryFn: () =>
      apiClient.get<AdminRevenueResponse>(`/admin/billing/revenue?period=${period}`),
    enabled: !!user && isAdmin,
  });

  const chartData = useMemo(
    () =>
      (q.data?.series ?? []).map((p) => ({
        label: p.label,
        amount: Math.round(p.amount_cents) / 100,
      })),
    [q.data?.series]
  );

  const growth = q.data?.growth_percent;
  const growthPositive = growth != null && growth > 0;
  const growthNegative = growth != null && growth < 0;

  if (user && !isAdmin) {
    return (
      <div className="flex h-48 items-center justify-center text-muted-foreground text-sm">
        Redirecting…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Revenue</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Paid payment totals and period-over-period growth (admin only).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Period</span>
          <Select value={period} onValueChange={(v) => setPeriod(v as RevenuePeriod)}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PERIODS.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total revenue ({PERIODS.find((p) => p.value === period)?.label})</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {q.isLoading ? (
                <Skeleton className="h-9 w-32" />
              ) : q.data ? (
                formatMoney(q.data.total_cents, q.data.currency)
              ) : (
                '—'
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Previous period</CardDescription>
            <CardTitle className="text-2xl tabular-nums">
              {q.isLoading ? (
                <Skeleton className="h-9 w-32" />
              ) : q.data?.previous_period_total_cents != null ? (
                formatMoney(q.data.previous_period_total_cents, q.data.currency)
              ) : (
                '—'
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5" />
              Growth vs previous period
            </CardDescription>
            <CardTitle className="text-2xl tabular-nums flex items-center gap-2">
              {q.isLoading ? (
                <Skeleton className="h-9 w-24" />
              ) : growth == null ? (
                <span className="text-muted-foreground text-lg font-normal">Not available</span>
              ) : (
                <>
                  {growthPositive && <ArrowUpRight className="h-6 w-6 text-emerald-600" />}
                  {growthNegative && <ArrowDownRight className="h-6 w-6 text-red-600" />}
                  {growth === 0 && <Minus className="h-6 w-6 text-muted-foreground" />}
                  <span
                    className={
                      growthPositive
                        ? 'text-emerald-600'
                        : growthNegative
                          ? 'text-red-600'
                          : 'text-muted-foreground'
                    }
                  >
                    {growth > 0 ? '+' : ''}
                    {growth.toFixed(1)}%
                  </span>
                </>
              )}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Revenue over time</CardTitle>
          <CardDescription>Bucket totals for the selected aggregation window</CardDescription>
        </CardHeader>
        <CardContent>
          {q.isLoading ? (
            <div className="flex h-72 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
              No paid payments in this range yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={288}>
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) =>
                    new Intl.NumberFormat(undefined, {
                      notation: 'compact',
                      maximumFractionDigits: 1,
                    }).format(v as number)
                  }
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    borderColor: 'hsl(var(--border))',
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                  formatter={(value: number) => {
                    const cur = (q.data?.currency ?? 'usd').toUpperCase();
                    const code = cur === 'XXX' ? 'USD' : cur;
                    return [
                      new Intl.NumberFormat(undefined, { style: 'currency', currency: code }).format(
                        value
                      ),
                      'Revenue',
                    ];
                  }}
                />
                <Bar
                  dataKey="amount"
                  name="Revenue"
                  fill="hsl(var(--primary))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
