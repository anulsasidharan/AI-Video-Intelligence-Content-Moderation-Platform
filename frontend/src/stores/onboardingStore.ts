import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingState {
  hasCompletedOnboarding: boolean;
  isRunning: boolean;
  stepIndex: number;
}

interface OnboardingActions {
  startTour: () => void;
  stopTour: () => void;
  completeTour: () => void;
  setStepIndex: (index: number) => void;
}

export const useOnboardingStore = create<OnboardingState & OnboardingActions>()(
  persist(
    (set) => ({
      // Persisted — survives page refresh
      hasCompletedOnboarding: false,
      // Transient — reset on every page load (excluded from partialize)
      isRunning: false,
      stepIndex: 0,

      startTour: () => set({ isRunning: true, stepIndex: 0 }),
      stopTour: () => set({ isRunning: false }),
      completeTour: () => set({ hasCompletedOnboarding: true, isRunning: false }),
      setStepIndex: (index) => set({ stepIndex: index }),
    }),
    {
      name: 'vidshield-onboarding',
      // Only persist the completion flag — never the transient running state
      partialize: (state) => ({
        hasCompletedOnboarding: state.hasCompletedOnboarding,
      }),
    }
  )
);
