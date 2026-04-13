'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import type { BeaconRenderProps, CallBackProps, Step, TooltipRenderProps } from 'react-joyride';
import { ACTIONS, EVENTS, STATUS } from 'react-joyride';
import {
  BarChart3,
  CheckCircle2,
  Radio,
  Shield,
  ShieldAlert,
  Upload,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useOnboardingStore } from '@/stores/onboardingStore';
import { useAuthStore } from '@/stores/authStore';
import { useAuth } from '@/hooks/useAuth';

// SSR-safe: react-joyride accesses window/document on import
const Joyride = dynamic(() => import('react-joyride'), { ssr: false });

// ── Custom beacon ─────────────────────────────────────────────────────────────

function TourBeacon(props: BeaconRenderProps) {
  return (
    <button
      {...props}
      aria-label="Open tour step"
      className="relative flex h-9 w-9 items-center justify-center focus:outline-none"
    >
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-50" />
      <span className="relative inline-flex h-4 w-4 rounded-full bg-primary shadow-md ring-2 ring-primary/30" />
    </button>
  );
}

// ── Custom tooltip ────────────────────────────────────────────────────────────

function TourTooltip({
  continuous,
  index,
  size,
  step,
  backProps,
  closeProps,
  primaryProps,
  skipProps,
  tooltipProps,
}: TooltipRenderProps) {
  const isFirst = index === 0;
  const isLast = index === size - 1;

  return (
    <div
      {...tooltipProps}
      className="w-[min(360px,92vw)] overflow-hidden rounded-xl border border-border bg-card text-card-foreground shadow-2xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b border-border bg-muted/40 px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <Shield className="h-4 w-4 shrink-0 text-primary" />
          {step.title && (
            <span className="truncate text-sm font-semibold">{step.title as string}</span>
          )}
        </div>
        <button
          {...(isLast ? closeProps : skipProps)}
          aria-label="Close tour"
          className="shrink-0 rounded-sm p-0.5 opacity-60 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="px-4 py-3 text-sm leading-relaxed text-muted-foreground">
        {step.content}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-border bg-muted/20 px-4 py-2.5">
        {/* Progress dots */}
        <div className="flex items-center gap-1.5">
          {Array.from({ length: size }).map((_, i) => (
            <span
              key={i}
              className={`inline-block rounded-full transition-all ${
                i === index
                  ? 'h-2 w-4 bg-primary'
                  : i < index
                    ? 'h-2 w-2 bg-primary/50'
                    : 'h-2 w-2 bg-muted-foreground/30'
              }`}
            />
          ))}
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-1.5">
          {!isFirst && !isLast && (
            <Button
              {...skipProps}
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs text-muted-foreground"
            >
              Skip
            </Button>
          )}
          {!isFirst && (
            <Button
              {...backProps}
              variant="outline"
              size="sm"
              className="h-7 px-3 text-xs"
            >
              Back
            </Button>
          )}
          <Button
            {...(isLast ? closeProps : primaryProps)}
            variant="default"
            size="sm"
            className="h-7 px-3 text-xs"
          >
            {isFirst ? "Let's Go" : isLast ? 'Finish' : continuous ? 'Next' : 'Close'}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Step definitions ──────────────────────────────────────────────────────────

const BASE_STEPS: Step[] = [
  // Step 1 — Welcome (centered modal)
  {
    target: 'body',
    placement: 'center',
    disableBeacon: true,
    title: 'Welcome to VidShield AI',
    content: (
      <div className="space-y-3">
        <div className="flex items-center justify-center py-2">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Shield className="h-7 w-7 text-primary" />
          </div>
        </div>
        <p className="text-center font-medium text-foreground">
          Your intelligent video content moderation platform
        </p>
        <p className="text-center text-xs">
          This quick tour walks you through the key features. It only takes about a minute.
        </p>
      </div>
    ),
  },

  // Step 2 — Dashboard overview
  {
    target: '[data-tour="nav-overview"]',
    placement: 'right',
    title: 'Dashboard Overview',
    content: (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-xs">
          <BarChart3 className="h-3.5 w-3.5 text-primary shrink-0" />
          <span>Your command center</span>
        </div>
        <p>
          Get a real-time snapshot of flagged content, AI moderation decisions, violation
          rates, and platform health — all from the Overview dashboard.
        </p>
      </div>
    ),
  },

  // Step 3 — Upload
  {
    target: '[data-tour="nav-upload"]',
    placement: 'right',
    title: 'Upload Videos',
    content: (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-xs">
          <Upload className="h-3.5 w-3.5 text-primary shrink-0" />
          <span>Supports MP4, WebM, MKV up to 5 GB</span>
        </div>
        <p>
          Drag-and-drop or browse to upload videos. AI analysis — scene detection, OCR,
          speech transcription, and safety scoring — begins automatically in the background.
        </p>
      </div>
    ),
  },

  // Step 4 — Moderation Queue
  {
    target: '[data-tour="nav-moderation"]',
    placement: 'right',
    title: 'AI Moderation Controls',
    content: (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-xs">
          <ShieldAlert className="h-3.5 w-3.5 text-primary shrink-0" />
          <span>Review AI-flagged content</span>
        </div>
        <p>
          Approve, reject, or escalate flagged items. Configure custom content policies
          under the Policies sub-section to tailor AI decisions to your community standards.
        </p>
      </div>
    ),
  },

  // Step 5 — Live Streams
  {
    target: '[data-tour="nav-live"]',
    placement: 'right',
    title: 'Live Stream Monitoring',
    content: (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-xs">
          <Radio className="h-3.5 w-3.5 text-red-500 shrink-0 animate-pulse" />
          <span>Real-time AI analysis</span>
        </div>
        <p>
          Monitor live streams frame-by-frame. Violations surface instantly with confidence
          scores via WebSocket so you can act before content spreads.
        </p>
      </div>
    ),
  },

  // Step 6 — Settings
  {
    target: '[data-tour="nav-settings"]',
    placement: 'right',
    title: 'Settings & Profile',
    content: (
      <p>
        Manage your account details, API keys, billing plan, and notification preferences
        here. You can also replay this tour from the Settings page anytime.
      </p>
    ),
  },

  // Step 7 — Completion (centered modal)
  {
    target: 'body',
    placement: 'center',
    disableBeacon: true,
    title: "You're all set!",
    content: (
      <div className="space-y-3">
        <div className="space-y-1.5">
          {[
            'Upload your first video for AI analysis',
            'Explore moderation policies',
            'Monitor live streams in real time',
          ].map((item) => (
            <div key={item} className="flex items-start gap-2 text-xs">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
              <span>{item}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground border-t border-border pt-2 mt-1">
          Replay this tour anytime from{' '}
          <strong className="text-foreground">Settings → Product Tour</strong>.
        </p>
      </div>
    ),
  },
];

// Admin-only step inserted at position 5 (after Live Streams, before Settings)
const REPORTS_STEP: Step = {
  target: '[data-tour="nav-reports"]',
  placement: 'right',
  title: 'Reports & Analytics',
  content: (
    <p>
      Generate compliance reports, view violation trends, and export audit data.
      The Explainability & Audit Trail gives full decision traceability for every
      AI action.
    </p>
  ),
};

// ── Main component ────────────────────────────────────────────────────────────

export function OnboardingTour() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { isAdmin } = useAuth();
  const { hasCompletedOnboarding, isRunning, stepIndex, startTour, stopTour, completeTour, setStepIndex } =
    useOnboardingStore();

  // Guard against Zustand rehydration race — mirrors the pattern in layout.tsx
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    setHydrated(true);
  }, []);

  // Auto-start for first-time users, after DOM has settled
  useEffect(() => {
    if (hydrated && isAuthenticated && !hasCompletedOnboarding && !isRunning) {
      const timer = setTimeout(() => startTour(), 700);
      return () => clearTimeout(timer);
    }
  // isRunning excluded intentionally — only fire once on mount
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated, hasCompletedOnboarding]);

  // Insert the Reports step for admins only
  const tourSteps = isAdmin
    ? [...BASE_STEPS.slice(0, 5), REPORTS_STEP, ...BASE_STEPS.slice(5)]
    : BASE_STEPS;

  const handleCallback = (data: CallBackProps) => {
    const { action, index, status, type } = data;

    if (type === EVENTS.STEP_AFTER) {
      const next = action === ACTIONS.PREV ? index - 1 : index + 1;
      setStepIndex(next);
    }

    if (type === EVENTS.TOUR_END) {
      if (status === STATUS.FINISHED) {
        completeTour();
      } else if (status === STATUS.SKIPPED) {
        stopTour();
      }
    }

    // Graceful fallback if a DOM target is missing (e.g., mobile hidden sidebar)
    if (status === STATUS.ERROR) {
      stopTour();
    }
  };

  if (!hydrated) return null;

  return (
    <Joyride
      steps={tourSteps}
      stepIndex={stepIndex}
      run={isRunning}
      continuous
      scrollToFirstStep
      disableScrolling={false}
      showProgress={false}
      showSkipButton={false}
      callback={handleCallback}
      tooltipComponent={TourTooltip}
      beaconComponent={TourBeacon}
      styles={{
        options: {
          arrowColor: 'transparent',
          overlayColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 10000,
          width: undefined,
          backgroundColor: 'transparent',
        },
        spotlight: {
          borderRadius: '8px',
          boxShadow: '0 0 0 2px hsl(var(--primary) / 0.4), 0 0 0 9999px rgba(0,0,0,0.5)',
        },
      }}
      floaterProps={{ disableAnimation: false, hideArrow: true }}
    />
  );
}
