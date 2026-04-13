import Image from 'next/image';
import {
  AlertTriangle,
  Clock,
  Zap,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatPercent, formatDuration } from '@/lib/utils';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';
import type { Violation } from '@/types/moderation';

const categoryColors: Record<string, string> = {
  violence: 'destructive',
  nudity: 'destructive',
  drugs: 'warning',
  hate_symbols: 'destructive',
  spam: 'secondary',
  misinformation: 'warning',
  other: 'secondary',
};

interface ViolationCardProps {
  violation: Violation;
  className?: string;
}

export function ViolationCard({ violation, className }: ViolationCardProps) {
  return (
    <Card className={className}>
      <CardContent className="p-4 space-y-3">
        {/* Frame thumbnail */}
        {violation.frame_url && (
          <div className="relative aspect-video w-full overflow-hidden rounded-md bg-muted">
            <Image
              src={violation.frame_url}
              alt="Violation frame"
              fill
              className="object-cover"
            />
          </div>
        )}

        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4 text-destructive shrink-0" />
            <Badge variant={(categoryColors[violation.category] as BadgeVariant) ?? 'secondary'}>
              {VIOLATION_CATEGORY_LABELS[violation.category]}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            <span>{formatPercent(violation.confidence)} confidence</span>
          </div>
          {violation.timestamp_seconds !== undefined && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>@ {formatDuration(violation.timestamp_seconds)}</span>
            </div>
          )}
        </div>

        {violation.snippet && (
          <p className="text-xs text-muted-foreground line-clamp-2 border-l-2 border-destructive/40 pl-2">
            {violation.snippet}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info';
