'use client';

import { Bell, Check, CheckCheck, Trash2, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { type AppNotification, useNotifications } from '@/hooks/useNotifications';

// ── Priority colour map ────────────────────────────────────────────────────────

const PRIORITY_DOT: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
};

const PRIORITY_LABEL_COLOR: Record<string, string> = {
  critical: 'text-red-500',
  high: 'text-orange-500',
  medium: 'text-yellow-500',
  low: 'text-blue-400',
};

// ── Single notification row ────────────────────────────────────────────────────

function NotificationRow({
  notification,
  onMarkRead,
  onDelete,
}: {
  notification: AppNotification;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const isUnread = notification.status !== 'read';

  return (
    <div
      className={cn(
        'flex items-start gap-3 px-3 py-2.5 hover:bg-muted/50 transition-colors',
        isUnread && 'bg-muted/20'
      )}
    >
      {/* Priority dot */}
      <span
        className={cn(
          'mt-1.5 h-2 w-2 shrink-0 rounded-full',
          PRIORITY_DOT[notification.priority] ?? 'bg-muted-foreground'
        )}
      />

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            'truncate text-xs',
            isUnread ? 'font-semibold text-foreground' : 'font-medium text-muted-foreground'
          )}
        >
          {notification.title}
        </p>
        <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">
          {notification.message}
        </p>
        <div className="mt-1 flex items-center gap-2">
          <span
            className={cn(
              'text-[10px] font-medium uppercase',
              PRIORITY_LABEL_COLOR[notification.priority]
            )}
          >
            {notification.priority}
          </span>
          <span className="text-[10px] text-muted-foreground">·</span>
          <span className="text-[10px] text-muted-foreground">
            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex shrink-0 flex-col gap-0.5">
        {isUnread && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-muted-foreground hover:text-foreground"
            title="Mark as read"
            onClick={() => onMarkRead(notification.id)}
          >
            <Check className="h-3 w-3" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-destructive"
          title="Delete"
          onClick={() => onDelete(notification.id)}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface NotificationCenterProps {
  className?: string;
}

export function NotificationCenter({ className }: NotificationCenterProps) {
  const {
    notifications,
    unreadCount,
    isLoading,
    markRead,
    markAllRead,
    deleteNotification,
    isMarkingAllRead,
  } = useNotifications();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn('relative', className)}
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 h-4 w-4 rounded-full p-0 text-[10px] flex items-center justify-center"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-96 p-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3">
          <DropdownMenuLabel className="p-0 text-sm font-semibold">
            Notifications
            {unreadCount > 0 && (
              <Badge variant="secondary" className="ml-2 text-[10px]">
                {unreadCount} unread
              </Badge>
            )}
          </DropdownMenuLabel>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
              onClick={() => markAllRead()}
              disabled={isMarkingAllRead}
            >
              <CheckCheck className="h-3 w-3" />
              Mark all read
            </Button>
          )}
        </div>
        <Separator />

        {/* Body */}
        {isLoading ? (
          <div className="space-y-2 p-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start gap-3">
                <Skeleton className="mt-1.5 h-2 w-2 shrink-0 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-2.5 w-1/3" />
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center text-muted-foreground">
            <Bell className="h-8 w-8 opacity-20" />
            <p className="text-sm">No notifications</p>
            <p className="text-xs opacity-70">
              You&apos;ll see alerts and updates here
            </p>
          </div>
        ) : (
          <ScrollArea className="max-h-80">
            {notifications.map((notif, idx) => (
              <div key={notif.id}>
                <NotificationRow
                  notification={notif}
                  onMarkRead={markRead}
                  onDelete={deleteNotification}
                />
                {idx < notifications.length - 1 && (
                  <Separator className="mx-3 w-auto" />
                )}
              </div>
            ))}
          </ScrollArea>
        )}

        {/* Footer */}
        {notifications.length > 0 && (
          <>
            <Separator />
            <div className="px-4 py-2 text-center">
              <p className="text-[11px] text-muted-foreground">
                Showing {notifications.length} notification
                {notifications.length !== 1 ? 's' : ''}
              </p>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
