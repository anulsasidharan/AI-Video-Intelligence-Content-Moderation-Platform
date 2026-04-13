'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow, format } from 'date-fns';
import {
  AlertTriangle,
  Bot,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  LogIn,
  LogOut,
  MonitorSmartphone,
  Network,
  XCircle,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AccessAuditLog {
  id: string;
  user_id: string | null;
  email: string;
  username: string | null;
  action: 'login' | 'logout';
  status: 'success' | 'failure';
  failure_reason: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

interface ViolationDetail {
  category: string | null;
  confidence: number | null;
  frame_ids: number[] | null;
  timestamps: number[] | null;
  rule: string | null;
  agent: string | null;
  description: string | null;
  severity: string | null;
}

interface ModerationAuditEntry {
  moderation_result_id: string;
  video_id: string;
  video_title: string;
  status: string;
  overall_confidence: number | null;
  ai_model: string | null;
  processing_time_ms: number | null;
  violations: ViolationDetail[];
  summary: string | null;
  reviewed_by_id: string | null;
  review_action: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
  override_decision: string | null;
  override_at: string | null;
  created_at: string;
}

/** Per-step AI pipeline audit row from GET /api/v1/admin/agent-audit */
interface AgentActivityLog {
  id: string;
  agent_id: string;
  action_type: string;
  description: string;
  input_ref: string;
  output_summary: string | null;
  status: 'SUCCESS' | 'FAILED' | 'IN_PROGRESS';
  execution_time_ms: number | null;
  triggered_by: string;
  trace_id: string;
  correlation_id: string | null;
  event_timestamp: string | null;
  created_at: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const FAILURE_REASON_LABELS: Record<string, string> = {
  user_not_found: 'User not found',
  invalid_password: 'Invalid password',
  account_blocked: 'Account permanently blocked',
  account_suspended: 'Account suspended',
};

const SEVERITY_COLOURS: Record<string, string> = {
  high: 'text-destructive border-destructive',
  medium: 'text-yellow-600 border-yellow-400',
  low: 'text-green-600 border-green-400',
};

// ── Access Audit tab ──────────────────────────────────────────────────────────

function AccessAuditTab() {
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [emailSearch, setEmailSearch] = useState('');
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data, isLoading } = useQuery({
    queryKey: ['audit-access', actionFilter, statusFilter, emailSearch, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (actionFilter !== 'all') params.set('action', actionFilter);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      if (emailSearch.trim()) params.set('email', emailSearch.trim());
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      return apiClient.get<{ items: AccessAuditLog[]; total: number }>(
        `/audit/access?${params.toString()}`
      );
    },
  });

  const totalPages = Math.ceil((data?.total ?? 0) / limit);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search by email…"
          className="w-56"
          value={emailSearch}
          onChange={(e) => { setEmailSearch(e.target.value); setPage(0); }}
        />
        <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v); setPage(0); }}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All actions</SelectItem>
            <SelectItem value="login">Login</SelectItem>
            <SelectItem value="logout">Logout</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0); }}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="failure">Failure</SelectItem>
          </SelectContent>
        </Select>
        {data && (
          <span className="ml-auto self-center text-sm text-muted-foreground">
            {data.total} record{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Failure reason</TableHead>
              <TableHead className="hidden lg:table-cell">
                <div className="flex items-center gap-1"><Network className="h-3.5 w-3.5" /> IP address</div>
              </TableHead>
              <TableHead className="hidden xl:table-cell">
                <div className="flex items-center gap-1"><MonitorSmartphone className="h-3.5 w-3.5" /> Device</div>
              </TableHead>
              <TableHead>Timestamp</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 8 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((__, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              : data?.items.map((log) => (
                  <TableRow key={log.id} className={log.status === 'failure' ? 'bg-destructive/5' : ''}>
                    <TableCell>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{log.username ?? '—'}</p>
                        <p className="text-xs text-muted-foreground truncate">{log.email}</p>
                        {log.user_id && (
                          <p className="text-[10px] font-mono text-muted-foreground truncate">{log.user_id}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5 text-sm">
                        {log.action === 'login'
                          ? <LogIn className="h-3.5 w-3.5 text-primary" />
                          : <LogOut className="h-3.5 w-3.5 text-muted-foreground" />}
                        <span className="capitalize">{log.action}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {log.status === 'success' ? (
                        <div className="flex items-center gap-1 text-green-600">
                          <CheckCircle className="h-3.5 w-3.5" />
                          <span className="text-xs font-medium">Success</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-destructive">
                          <XCircle className="h-3.5 w-3.5" />
                          <span className="text-xs font-medium">Failure</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {log.failure_reason ? (
                        <Badge variant="outline" className="text-xs text-destructive border-destructive/50">
                          {FAILURE_REASON_LABELS[log.failure_reason] ?? log.failure_reason}
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-xs font-mono text-muted-foreground">
                      {log.ip_address ?? '—'}
                    </TableCell>
                    <TableCell className="hidden xl:table-cell">
                      <span className="text-xs text-muted-foreground truncate max-w-[200px] block" title={log.user_agent ?? ''}>
                        {log.user_agent ? log.user_agent.substring(0, 60) + (log.user_agent.length > 60 ? '…' : '') : '—'}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      <span title={format(new Date(log.created_at), 'PPpp')}>
                        {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Page {page + 1} of {totalPages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => p - 1)} disabled={page === 0}>
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage((p) => p + 1)} disabled={page >= totalPages - 1}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Moderation Audit tab ─────────────────────────────────────────────────────

function ViolationRow({ v, index }: { v: ViolationDetail; index: number }) {
  return (
    <div className="rounded border bg-muted/30 p-3 space-y-1.5 text-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-medium capitalize">{v.category ?? 'Unknown category'}</span>
        {v.severity && (
          <Badge variant="outline" className={cn('text-xs', SEVERITY_COLOURS[v.severity] ?? '')}>
            {v.severity}
          </Badge>
        )}
        {v.confidence !== null && v.confidence !== undefined && (
          <Badge variant="secondary" className="text-xs">
            {(v.confidence * 100).toFixed(1)}% confidence
          </Badge>
        )}
        <span className="text-xs text-muted-foreground ml-auto">Finding #{index + 1}</span>
      </div>
      {v.agent && (
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Agent:</span> {v.agent}
        </p>
      )}
      {v.rule && (
        <p className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Rule:</span> {v.rule}
        </p>
      )}
      {v.description && (
        <p className="text-xs text-muted-foreground">{v.description}</p>
      )}
      {v.frame_ids && v.frame_ids.length > 0 && (
        <p className="text-xs text-muted-foreground font-mono">
          <span className="font-medium text-foreground not-italic">Frames:</span>{' '}
          {v.frame_ids.slice(0, 10).join(', ')}{v.frame_ids.length > 10 ? ` … +${v.frame_ids.length - 10} more` : ''}
        </p>
      )}
      {v.timestamps && v.timestamps.length > 0 && (
        <p className="text-xs text-muted-foreground font-mono">
          <span className="font-medium text-foreground not-italic">Timestamps (s):</span>{' '}
          {v.timestamps.slice(0, 8).map((t) => t.toFixed(2)).join(', ')}{v.timestamps.length > 8 ? ' …' : ''}
        </p>
      )}
    </div>
  );
}

function ModerationAuditRow({ entry }: { entry: ModerationAuditEntry }) {
  const [expanded, setExpanded] = useState(false);

  const statusColour =
    entry.status === 'approved' ? 'text-green-600 border-green-400' :
    entry.status === 'rejected' ? 'text-destructive border-destructive' :
    entry.status === 'flagged' ? 'text-yellow-600 border-yellow-400' :
    entry.status === 'escalated' ? 'text-orange-600 border-orange-400' : '';

  return (
    <>
      <TableRow
        className="cursor-pointer hover:bg-muted/40"
        onClick={() => setExpanded((e) => !e)}
      >
        <TableCell>
          {expanded
            ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
            : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        </TableCell>
        <TableCell>
          <p className="text-sm font-medium truncate max-w-[200px]" title={entry.video_title}>
            {entry.video_title}
          </p>
          <p className="text-xs font-mono text-muted-foreground">{entry.video_id.slice(0, 8)}…</p>
        </TableCell>
        <TableCell>
          <Badge variant="outline" className={cn('capitalize text-xs', statusColour)}>
            {entry.status}
          </Badge>
        </TableCell>
        <TableCell>
          {entry.violations.length > 0 ? (
            <div className="flex items-center gap-1 text-destructive">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">{entry.violations.length} violation{entry.violations.length !== 1 ? 's' : ''}</span>
            </div>
          ) : (
            <span className="text-xs text-muted-foreground">No violations</span>
          )}
        </TableCell>
        <TableCell className="text-xs text-muted-foreground">
          {entry.ai_model ?? '—'}
        </TableCell>
        <TableCell className="text-xs text-muted-foreground">
          {entry.overall_confidence !== null
            ? `${((entry.overall_confidence ?? 0) * 100).toFixed(1)}%`
            : '—'}
        </TableCell>
        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
          <span title={format(new Date(entry.created_at), 'PPpp')}>
            {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
          </span>
        </TableCell>
      </TableRow>

      {expanded && (
        <TableRow>
          <TableCell colSpan={7} className="bg-muted/20 px-6 py-4">
            <div className="space-y-4">

              {/* Summary */}
              {entry.summary && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">AI Summary</p>
                  <p className="text-sm">{entry.summary}</p>
                </div>
              )}

              {/* Violations */}
              {entry.violations.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    Violations — frames, rules &amp; agents
                  </p>
                  <div className="space-y-2">
                    {entry.violations.map((v, i) => (
                      <ViolationRow key={i} v={v} index={i} />
                    ))}
                  </div>
                </div>
              )}

              {/* Review / Override */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                {entry.review_action && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Human Review</p>
                    <p><span className="text-muted-foreground">Action:</span> <span className="capitalize">{entry.review_action}</span></p>
                    {entry.review_notes && <p><span className="text-muted-foreground">Notes:</span> {entry.review_notes}</p>}
                    {entry.reviewed_at && <p><span className="text-muted-foreground">At:</span> {entry.reviewed_at}</p>}
                  </div>
                )}
                {entry.override_decision && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Admin Override</p>
                    <p><span className="text-muted-foreground">Decision:</span> {entry.override_decision}</p>
                    {entry.override_at && <p><span className="text-muted-foreground">At:</span> {entry.override_at}</p>}
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="flex gap-4 text-xs text-muted-foreground font-mono">
                <span>Result ID: {entry.moderation_result_id}</span>
                {entry.processing_time_ms && <span>Processing: {entry.processing_time_ms}ms</span>}
              </div>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function ModerationAuditTab() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(0);
  const limit = 50;

  const { data, isLoading } = useQuery({
    queryKey: ['audit-moderation', statusFilter, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.set('status', statusFilter);
      params.set('skip', String(page * limit));
      params.set('limit', String(limit));
      return apiClient.get<{ items: ModerationAuditEntry[]; total: number }>(
        `/audit/moderation?${params.toString()}`
      );
    },
  });

  const totalPages = Math.ceil((data?.total ?? 0) / limit);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0); }}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="flagged">Flagged</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="escalated">Escalated</SelectItem>
          </SelectContent>
        </Select>
        {data && (
          <span className="ml-auto self-center text-sm text-muted-foreground">
            {data.total} record{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Click a row to expand violation details — frames, rules, and agents that produced each finding.
      </p>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Video</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Violations</TableHead>
              <TableHead>AI Model</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Analysed</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((__, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              : data?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-sm text-muted-foreground py-10">
                      No moderation records found.
                    </TableCell>
                  </TableRow>
                )
              : data?.items.map((entry) => (
                  <ModerationAuditRow key={entry.moderation_result_id} entry={entry} />
                ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Page {page + 1} of {totalPages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => p - 1)} disabled={page === 0}>
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage((p) => p + 1)} disabled={page >= totalPages - 1}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Agent Audit (AI pipeline activity) ───────────────────────────────────────

const AGENT_AUDIT_STATUS_OPTIONS = ['all', 'SUCCESS', 'FAILED', 'IN_PROGRESS'] as const;

function AgentAuditStatusBadge({ status }: { status: AgentActivityLog['status'] }) {
  const cls =
    status === 'SUCCESS'
      ? 'text-green-600 border-green-400'
      : status === 'FAILED'
        ? 'text-destructive border-destructive'
        : 'text-amber-600 border-amber-400';
  return (
    <Badge variant="outline" className={cn('text-xs font-mono', cls)}>
      {status}
    </Badge>
  );
}

function AgentAuditRow({ entry }: { entry: AgentActivityLog }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <>
      <TableRow
        className="cursor-pointer hover:bg-muted/40"
        onClick={() => setExpanded((e) => !e)}
      >
        <TableCell className="w-8">
          {expanded
            ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
            : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        </TableCell>
        <TableCell>
          <span className="text-sm font-mono">{entry.agent_id}</span>
        </TableCell>
        <TableCell>
          <span className="text-xs font-mono">{entry.action_type}</span>
        </TableCell>
        <TableCell className="max-w-[220px]">
          <span className="text-xs line-clamp-2" title={entry.description}>{entry.description}</span>
        </TableCell>
        <TableCell>
          <span className="text-xs font-mono truncate max-w-[120px] block" title={entry.input_ref}>
            {entry.input_ref}
          </span>
        </TableCell>
        <TableCell>
          <AgentAuditStatusBadge status={entry.status} />
        </TableCell>
        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
          {entry.execution_time_ms != null ? `${entry.execution_time_ms} ms` : '—'}
        </TableCell>
        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
          <span title={format(new Date(entry.created_at), 'PPpp')}>
            {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
          </span>
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow>
          <TableCell colSpan={8} className="bg-muted/20 px-6 py-4">
            <div className="space-y-3 text-sm">
              <div className="grid gap-2 sm:grid-cols-2">
                <p><span className="text-muted-foreground">Triggered by:</span> {entry.triggered_by}</p>
                <p className="font-mono text-xs break-all">
                  <span className="text-muted-foreground">Trace ID:</span> {entry.trace_id}
                </p>
                {entry.correlation_id && (
                  <p className="font-mono text-xs break-all sm:col-span-2">
                    <span className="text-muted-foreground">Correlation ID:</span> {entry.correlation_id}
                  </p>
                )}
                {entry.output_summary && (
                  <p className="sm:col-span-2">
                    <span className="text-muted-foreground">Output summary:</span> {entry.output_summary}
                  </p>
                )}
                {entry.event_timestamp && (
                  <p className="sm:col-span-2 text-xs text-muted-foreground">
                    Event time: {format(new Date(entry.event_timestamp), 'PPpp')}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Raw record (JSON)</p>
                <pre className="text-[11px] font-mono bg-muted/50 rounded-md p-3 overflow-x-auto max-h-64 overflow-y-auto">
                  {JSON.stringify(entry, null, 2)}
                </pre>
              </div>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function AgentAuditTab() {
  const [agentIdFilter, setAgentIdFilter] = useState('');
  const [actionTypeFilter, setActionTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const limit = 50;

  const { data, isLoading, isError } = useQuery({
    queryKey: [
      'audit-agent-activity',
      agentIdFilter,
      actionTypeFilter,
      statusFilter,
      startDate,
      endDate,
      page,
    ],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('page', String(page));
      params.set('limit', String(limit));
      if (agentIdFilter.trim()) params.set('agent_id', agentIdFilter.trim());
      if (actionTypeFilter.trim()) params.set('action_type', actionTypeFilter.trim());
      if (statusFilter !== 'all') params.set('status', statusFilter);
      if (startDate) params.set('start_date', `${startDate}T00:00:00.000Z`);
      if (endDate) params.set('end_date', `${endDate}T23:59:59.999Z`);
      return apiClient.get<{ items: AgentActivityLog[]; total: number }>(
        `/admin/agent-audit?${params.toString()}`
      );
    },
  });

  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / limit));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Agent ID</label>
          <Input
            placeholder="e.g. orchestrator"
            className="w-44"
            value={agentIdFilter}
            onChange={(e) => { setAgentIdFilter(e.target.value); setPage(1); }}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Action type</label>
          <Input
            placeholder="e.g. CONTENT_MODERATION"
            className="w-48"
            value={actionTypeFilter}
            onChange={(e) => { setActionTypeFilter(e.target.value); setPage(1); }}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Status</label>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              {AGENT_AUDIT_STATUS_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  {s === 'all' ? 'All statuses' : s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">From</label>
          <Input
            type="date"
            className="w-40"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">To</label>
          <Input
            type="date"
            className="w-40"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
          />
        </div>
        {data !== undefined && (
          <span className="ml-auto text-sm text-muted-foreground pb-2">
            {data.total} record{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <p className="text-xs text-muted-foreground flex items-center gap-1.5">
        <Bot className="h-3.5 w-3.5" />
        Structured log of AI agent steps (orchestrator, analyzers, safety, report). Rows appear after the pipeline writes audit events to the database.
      </p>

      {isError && (
        <p className="text-sm text-destructive">Could not load agent audit logs. Ensure you are signed in as an admin.</p>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Agent</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Input ref</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Logged</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 8 }).map((__, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              : data?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-sm text-muted-foreground py-10">
                      No agent activity logged yet. Process a video through the AI pipeline to populate this view.
                    </TableCell>
                  </TableRow>
                )
              : data?.items.map((entry) => (
                  <AgentAuditRow key={entry.id} entry={entry} />
                ))}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AuditTrailPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Explainability &amp; Audit Trail</h1>
        <p className="text-muted-foreground">
          Moderation outcomes, AI pipeline activity, and access events (admin only).
        </p>
      </div>

      <Tabs defaultValue="moderation">
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="moderation">Moderation Audit</TabsTrigger>
          <TabsTrigger value="agent" className="gap-1">
            <Bot className="h-3.5 w-3.5" />
            Agent Audit
          </TabsTrigger>
          <TabsTrigger value="access">Access Audit</TabsTrigger>
        </TabsList>

        {/* ── Moderation Audit ─────────────────────────────────────────── */}
        <TabsContent value="moderation" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Moderation Audit</CardTitle>
              <CardDescription>
                Per-video moderation outcomes and explainability — violations, frames, rules, and AI components that produced each finding.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ModerationAuditTab />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Agent Audit (pipeline steps) ─────────────────────────────── */}
        <TabsContent value="agent" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                Agent Audit
              </CardTitle>
              <CardDescription>
                Step-by-step AI agent activity: agent, action, input reference, outcome, timing, and trace IDs for debugging multi-agent runs.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AgentAuditTab />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Access Audit ─────────────────────────────────────────────── */}
        <TabsContent value="access" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Access Audit</CardTitle>
              <CardDescription>
                Every login and logout event — username, timestamp, IP address, device, and failure reasons.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AccessAuditTab />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
