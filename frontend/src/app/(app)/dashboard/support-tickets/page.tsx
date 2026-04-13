'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow, format } from 'date-fns';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Headphones,
  Loader2,
  MessageSquare,
  Phone,
  RefreshCw,
  Mail,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';

// ── Types ──────────────────────────────────────────────────────────────────────

interface SupportTicket {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  subject: string;
  message: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high';
  admin_notes: string | null;
  created_at: string;
  updated_at: string;
}

interface TicketListResponse {
  items: SupportTicket[];
  total: number;
  page: number;
  page_size: number;
}

// ── Config ─────────────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  open: { label: 'Open', icon: Clock, className: 'bg-amber-100 text-amber-700 border-amber-200' },
  in_progress: { label: 'In Progress', icon: Loader2, className: 'bg-blue-100 text-blue-700 border-blue-200' },
  resolved: { label: 'Resolved', icon: CheckCircle2, className: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  closed: { label: 'Closed', icon: AlertCircle, className: 'bg-slate-100 text-slate-600 border-slate-200' },
} as const;

const PRIORITY_CONFIG = {
  low: { label: 'Low', className: 'bg-slate-100 text-slate-600 border-slate-200' },
  medium: { label: 'Medium', className: 'bg-blue-100 text-blue-700 border-blue-200' },
  high: { label: 'High', className: 'bg-red-100 text-red-700 border-red-200' },
} as const;

// ── Component ──────────────────────────────────────────────────────────────────

export default function SupportTicketsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [newPriority, setNewPriority] = useState('');
  const [adminNotes, setAdminNotes] = useState('');

  const { data, isLoading, isFetching, refetch } = useQuery<TicketListResponse>({
    queryKey: ['support-tickets', statusFilter, page],
    queryFn: () =>
      apiClient.get<TicketListResponse>('/support-tickets', {
        params: {
          page,
          page_size: 20,
          ...(statusFilter !== 'all' && { status: statusFilter }),
        },
      }),
    refetchInterval: 30_000,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status, priority, notes }: { id: string; status: string; priority: string; notes: string }) =>
      apiClient.patch(`/support-tickets/${id}`, { status, priority, admin_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] });
      setSelectedTicket(null);
    },
  });

  const tickets = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  const openTicket = (t: SupportTicket) => {
    setSelectedTicket(t);
    setNewStatus(t.status);
    setNewPriority(t.priority);
    setAdminNotes(t.admin_notes ?? '');
  };

  const statusCounts = {
    open: tickets.filter((t) => t.status === 'open').length,
    in_progress: tickets.filter((t) => t.status === 'in_progress').length,
    resolved: tickets.filter((t) => t.status === 'resolved').length,
    closed: tickets.filter((t) => t.status === 'closed').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Support Tickets</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage customer support requests submitted via the support form.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-1.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {(Object.entries(STATUS_CONFIG) as [keyof typeof STATUS_CONFIG, typeof STATUS_CONFIG[keyof typeof STATUS_CONFIG]][]).map(([key, cfg]) => {
          const Icon = cfg.icon;
          return (
            <Card key={key} className="py-4">
              <CardContent className="flex items-center gap-3 px-4">
                <Icon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold">{statusCounts[key]}</p>
                  <p className="text-xs text-muted-foreground">{cfg.label}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tickets table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Tickets</CardTitle>
              <CardDescription>{total} total request(s)</CardDescription>
            </div>
            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
              <Headphones className="h-10 w-10 opacity-30" />
              <p className="text-sm">No support tickets yet.</p>
            </div>
          ) : (
            <div className="divide-y">
              {tickets.map((ticket) => {
                const sc = STATUS_CONFIG[ticket.status];
                const pc = PRIORITY_CONFIG[ticket.priority];
                const Icon = sc.icon;
                return (
                  <div
                    key={ticket.id}
                    className="flex items-start gap-4 px-6 py-4 hover:bg-muted/30 cursor-pointer transition-colors"
                    onClick={() => openTicket(ticket)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-sm truncate">{ticket.subject}</span>
                        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${sc.className}`}>
                          <Icon className="h-3 w-3" />
                          {sc.label}
                        </span>
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${pc.className}`}>
                          {pc.label}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {ticket.name} · {ticket.email}
                        </span>
                        {ticket.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {ticket.phone}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground shrink-0">
                      {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}

      {/* Detail dialog */}
      {selectedTicket && (
        <Dialog open onOpenChange={(o) => !o && setSelectedTicket(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-left pr-6">{selectedTicket.subject}</DialogTitle>
            </DialogHeader>

            <div className="space-y-4 pt-2">
              {/* Meta */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground text-xs">From</span>
                  <div className="font-medium">{selectedTicket.name}</div>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">Submitted</span>
                  <div className="font-medium">
                    {format(new Date(selectedTicket.created_at), 'MMM d, yyyy HH:mm')}
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                  <a href={`mailto:${selectedTicket.email}`} className="text-blue-600 hover:underline">
                    {selectedTicket.email}
                  </a>
                </div>
                {selectedTicket.phone && (
                  <div className="flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>{selectedTicket.phone}</span>
                  </div>
                )}
              </div>

              {/* Message */}
              <div>
                <span className="text-xs text-muted-foreground flex items-center gap-1 mb-1.5">
                  <MessageSquare className="h-3 w-3" /> Message
                </span>
                <div className="bg-muted/40 rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
                  {selectedTicket.message}
                </div>
              </div>

              {/* Update form */}
              <div className="border-t pt-4 space-y-3">
                <p className="text-sm font-medium">Update ticket</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block">Status</label>
                    <Select value={newStatus} onValueChange={setNewStatus}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">Open</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="resolved">Resolved</SelectItem>
                        <SelectItem value="closed">Closed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block">Priority</label>
                    <Select value={newPriority} onValueChange={setNewPriority}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Admin notes (internal)</label>
                  <Textarea
                    value={adminNotes}
                    onChange={(e) => setAdminNotes(e.target.value)}
                    placeholder="Internal notes — not visible to the customer"
                    rows={3}
                  />
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setSelectedTicket(null)}>
                Cancel
              </Button>
              <Button
                disabled={updateMutation.isPending}
                onClick={() =>
                  updateMutation.mutate({
                    id: selectedTicket.id,
                    status: newStatus,
                    priority: newPriority,
                    notes: adminNotes,
                  })
                }
              >
                {updateMutation.isPending ? (
                  <><Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Saving…</>
                ) : (
                  'Save changes'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
