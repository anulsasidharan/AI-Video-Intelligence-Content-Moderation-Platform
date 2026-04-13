import { create } from 'zustand';
import type { ModerationQueueItem, ModerationStatus, Policy } from '@/types/moderation';

interface ModerationState {
  selectedQueueItemId: string | null;
  queueFilter: ModerationStatus | 'all';
  activePolicyId: string | null;
  liveAlerts: LiveAlert[];
}

interface LiveAlert {
  id: string;
  stream_id?: string;
  video_id?: string;
  category: string;
  confidence: number;
  timestamp: string;
  dismissed: boolean;
}

interface ModerationActions {
  selectQueueItem: (id: string | null) => void;
  setQueueFilter: (filter: ModerationStatus | 'all') => void;
  setActivePolicy: (id: string | null) => void;
  addLiveAlert: (alert: Omit<LiveAlert, 'dismissed'>) => void;
  dismissAlert: (id: string) => void;
  clearAlerts: () => void;
}

export const useModerationStore = create<ModerationState & ModerationActions>()(
  (set) => ({
    selectedQueueItemId: null,
    queueFilter: 'all',
    activePolicyId: null,
    liveAlerts: [],

    selectQueueItem: (id) => set({ selectedQueueItemId: id }),

    setQueueFilter: (filter) => set({ queueFilter: filter }),

    setActivePolicy: (id) => set({ activePolicyId: id }),

    addLiveAlert: (alert) =>
      set((state) => ({
        liveAlerts: [{ ...alert, dismissed: false }, ...state.liveAlerts].slice(
          0,
          50
        ),
      })),

    dismissAlert: (id) =>
      set((state) => ({
        liveAlerts: state.liveAlerts.map((a) =>
          a.id === id ? { ...a, dismissed: true } : a
        ),
      })),

    clearAlerts: () => set({ liveAlerts: [] }),
  })
);

export const selectUndismissedAlerts = (
  state: ModerationState & ModerationActions
) => state.liveAlerts.filter((a) => !a.dismissed);
