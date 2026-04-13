'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowUpRight, Check, Loader2, Mail, Settings, Sparkles, Zap } from 'lucide-react';
import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import type { CheckoutSessionResponse, PortalSessionResponse, SubscriptionView } from '@/types/billing';

function PricingBanners({ onSuccess }: { onSuccess: () => void }) {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const success = searchParams.get('success');
    const canceled = searchParams.get('canceled');
    if (success === 'true') {
      apiClient
        .post<SubscriptionView>('/billing/sync')
        .then(() => {
          onSuccess();
          toast.success('Payment successful! Your plan has been updated.');
        })
        .catch(() => {
          onSuccess();
          toast.success('Payment successful! Refreshing your plan...');
        });
      router.replace('/dashboard/pricing');
    } else if (canceled === 'true') {
      toast.info('Checkout canceled — no charge was made.');
      router.replace('/dashboard/pricing');
    }
  }, [searchParams, router, onSuccess]);

  return null;
}

interface PlanConfig {
  key: string;
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  highlight: boolean;
  trial?: string;
}

const PLANS: PlanConfig[] = [
  {
    key: 'free',
    name: 'Free',
    price: '$0',
    period: '/month',
    description: 'Get started with basic AI video moderation at no cost.',
    features: [
      'Up to 10 videos / month',
      'Standard AI moderation',
      'Basic content reports',
      'REST API access',
      'Email support',
    ],
    cta: 'Current Plan',
    highlight: false,
  },
  {
    key: 'starter',
    name: 'Starter',
    price: '$299',
    period: '/month',
    description: 'For growing platforms needing reliable automated moderation.',
    trial: '14-day free trial',
    features: [
      'Up to 10,000 video minutes / month',
      'GPT-4o vision analysis',
      'Full moderation reports & PDF export',
      'Webhook notifications',
      'Priority email support',
      'API access',
      '7-day report retention',
    ],
    cta: 'Start Free Trial',
    highlight: false,
  },
  {
    key: 'growth',
    name: 'Growth',
    price: '$999',
    period: '/month',
    description: 'For high-volume platforms requiring advanced intelligence.',
    trial: '14-day free trial',
    features: [
      'Unlimited video minutes',
      'Live stream moderation',
      'Unlimited moderation policies',
      'Dedicated Slack support',
      'SLA guarantee',
      'Advanced analytics & revenue reports',
      '90-day report retention',
    ],
    cta: 'Start Free Trial',
    highlight: true,
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'Tailored deployments for enterprise-scale requirements.',
    features: [
      'All Growth features',
      'On-premise / VPC deployment',
      'Custom SLA & uptime guarantees',
      'Dedicated account manager',
      'Custom AI fine-tuning',
      'SSO / SAML integration',
      'Volume discounts',
    ],
    cta: 'Contact Sales',
    highlight: false,
  },
];

const PAID_PLANS = ['starter', 'growth'];

export default function PricingPage() {
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const queryClient = useQueryClient();

  const handleSyncSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['billing', 'subscription'] });
    queryClient.invalidateQueries({ queryKey: ['billing', 'payments'] });
  };

  const subQ = useQuery({
    queryKey: ['billing', 'subscription'],
    queryFn: () => apiClient.get<SubscriptionView>('/billing/subscription'),
  });

  const currentPlan = subQ.data?.plan_key ?? 'free';
  const isOnPaidPlan = PAID_PLANS.includes(currentPlan);

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

  const handleUpgrade = async (planKey: string) => {
    if (planKey === 'enterprise') {
      window.location.href = 'mailto:sales@orionvexa.ca?subject=VidShield%20Enterprise%20Enquiry';
      return;
    }
    if (planKey === 'free' || planKey === currentPlan) return;

    // If already on a paid plan, send to portal to change/cancel instead of new checkout
    if (isOnPaidPlan) {
      toast.info(`You already have an active ${currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)} subscription. Use the billing portal to change or cancel your plan.`);
      await handleManageBilling();
      return;
    }

    setLoadingPlan(planKey);
    try {
      const resp = await apiClient.post<CheckoutSessionResponse>('/billing/checkout', {
        plan: planKey,
      });
      window.location.href = resp.checkout_url;
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not start checkout. Please try again.');
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <Suspense fallback={null}>
        <PricingBanners onSuccess={handleSyncSuccess} />
      </Suspense>

      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">Choose your plan</h1>
        </div>
        <p className="text-muted-foreground max-w-xl mx-auto">
          Start free, upgrade when you need more. Paid plans include a{' '}
          <span className="text-foreground font-medium">14-day free trial</span> — no credit card
          required.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan) => {
          const isCurrent = plan.key === currentPlan;
          const isLoading = loadingPlan === plan.key;
          const isPaid = PAID_PLANS.includes(plan.key);
          const isDisabled =
            isCurrent || plan.key === 'free' || isLoading || loadingPlan !== null || portalLoading;

          return (
            <Card
              key={plan.key}
              className={`relative flex flex-col ${
                plan.highlight
                  ? 'border-primary shadow-md ring-1 ring-primary'
                  : ''
              } ${isCurrent ? 'ring-1 ring-muted-foreground/30' : ''}`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="gap-1 px-3 py-1">
                    <Zap className="h-3 w-3" />
                    Most Popular
                  </Badge>
                </div>
              )}
              {isCurrent && !plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="secondary" className="px-3 py-1 text-xs">
                    Your Plan
                  </Badge>
                </div>
              )}
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{plan.name}</CardTitle>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  {plan.period && (
                    <span className="text-sm text-muted-foreground">{plan.period}</span>
                  )}
                </div>
                {plan.trial && (
                  <p className="text-xs font-medium text-green-600 dark:text-green-400">
                    {plan.trial} · no card required
                  </p>
                )}
                <CardDescription className="text-sm">{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="flex-1">
                <ul className="space-y-2">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      {f}
                    </li>
                  ))}
                </ul>
              </CardContent>

              <CardFooter>
                {isCurrent ? (
                  // Currently active plan
                  isOnPaidPlan ? (
                    <Button
                      variant="outline"
                      className="w-full gap-1.5"
                      onClick={handleManageBilling}
                      disabled={portalLoading}
                    >
                      {portalLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Settings className="h-4 w-4" />
                      )}
                      Manage / Cancel
                    </Button>
                  ) : (
                    <Button variant="secondary" className="w-full" disabled>
                      Current Plan
                    </Button>
                  )
                ) : plan.key === 'enterprise' ? (
                  <Button
                    variant="outline"
                    className="w-full gap-1.5"
                    onClick={() => handleUpgrade('enterprise')}
                  >
                    <Mail className="h-4 w-4" />
                    {plan.cta}
                  </Button>
                ) : isOnPaidPlan && isPaid ? (
                  // User is on a paid plan — show "Switch Plan" via portal, not new checkout
                  <Button
                    variant={plan.highlight ? 'default' : 'outline'}
                    className="w-full gap-1.5"
                    onClick={handleManageBilling}
                    disabled={portalLoading}
                  >
                    {portalLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ArrowUpRight className="h-4 w-4" />
                    )}
                    Switch Plan
                  </Button>
                ) : (
                  <Button
                    className="w-full"
                    variant={plan.highlight ? 'default' : 'outline'}
                    disabled={isDisabled}
                    onClick={() => handleUpgrade(plan.key)}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Redirecting to checkout...
                      </>
                    ) : (
                      plan.cta
                    )}
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>

      <p className="text-center text-xs text-muted-foreground">
        All prices in USD · Monthly billing · Cancel anytime from your billing portal · Free plan
        is always free
      </p>
    </div>
  );
}
