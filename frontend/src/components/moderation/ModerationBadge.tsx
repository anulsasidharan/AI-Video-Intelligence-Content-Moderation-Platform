import { Badge, type BadgeProps } from '@/components/ui/badge';
import { MODERATION_STATUS_LABELS } from '@/lib/constants';
import type { ModerationStatus } from '@/types/moderation';

const variantMap: Record<ModerationStatus, BadgeProps['variant']> = {
  pending: 'secondary',
  in_review: 'info',
  approved: 'success',
  rejected: 'destructive',
  escalated: 'warning',
  flagged: 'warning',
};

interface ModerationBadgeProps {
  status: ModerationStatus;
  className?: string;
}

export function ModerationBadge({ status, className }: ModerationBadgeProps) {
  return (
    <Badge variant={variantMap[status]} className={className}>
      {MODERATION_STATUS_LABELS[status]}
    </Badge>
  );
}
