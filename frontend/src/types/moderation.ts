export type ModerationStatus =
  | 'pending'
  | 'in_review'
  | 'approved'
  | 'rejected'
  | 'escalated'
  | 'flagged';

export type ViolationCategory =
  | 'violence'
  | 'nudity'
  | 'drugs'
  | 'hate_symbols'
  | 'spam'
  | 'misinformation'
  | 'other';

export type ReviewAction = 'approve' | 'reject' | 'escalate';

export type PolicyAction = 'block' | 'flag' | 'allow';

export interface Violation {
  id: string;
  category: ViolationCategory;
  timestamp_seconds?: number;
  confidence: number;
  snippet?: string;
  frame_url?: string;
  details?: Record<string, unknown>;
}

export interface ModerationReport {
  violations: Violation[];
  recommended_action: ReviewAction;
  policy_id?: string;
  summary?: string;
  processed_at: string;
}

// Per-violation finding from the AI pipeline
export interface AiViolation {
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  timestamp: number;
  description: string;
  frame_index?: number;
}

export interface ModerationQueueItem {
  id: string;
  video_id?: string;
  stream_id?: string;
  moderation_result_id?: string;
  status: ModerationStatus;
  priority: number;
  report?: ModerationReport; // legacy field
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  created_at: string;
  updated_at?: string;
  // Joined from ModerationResult — AI justification
  video_title?: string;
  ai_summary?: string;
  overall_confidence?: number;
  violations?: AiViolation[];
  ai_model?: string;
}

export interface ModerationQueueResponse {
  items: ModerationQueueItem[];
  total: number;
  page: number;
  page_size: number;
}

export type ModerationResultResponse = ModerationQueueItem;

export interface SubmitReviewRequest {
  action: ReviewAction;
  notes?: string;
}

export interface PolicyRule {
  category: ViolationCategory;
  threshold: number;
  action: PolicyAction;
}

export interface Policy {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  is_default: boolean;
  rules: PolicyRule[] | null;
  default_action: PolicyAction;
  owner_id: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  items: Policy[];
  total: number;
}

export type PolicyResponse = Policy;

export interface CreatePolicyRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  is_default?: boolean;
  rules?: PolicyRule[];
  default_action?: PolicyAction;
}

export interface ModerationQueueParams {
  page?: number;
  page_size?: number;
  status?: ModerationStatus;
  priority?: number;
}
