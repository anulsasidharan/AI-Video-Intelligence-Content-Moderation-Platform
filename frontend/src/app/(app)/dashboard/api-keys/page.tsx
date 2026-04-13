'use client';

import { useEffect, useMemo, useState } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import type { LucideIcon } from 'lucide-react';
import {
  AlertTriangle,
  BookOpen,
  Check,
  Code2,
  Copy,
  KeyRound,
  Loader2,
  Lock,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCw,
  Shield,
  ShieldAlert,
  Trash2,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';
import { useApiKeys, useCreateApiKey, useRenameApiKey, useRevokeApiKey } from '@/hooks/useApiKeys';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_BASE_URL, API_V1 } from '@/lib/constants';
import { getBrowserApiV1Root } from '@/lib/apiOrigin';
import type { ApiKey, CreateApiKeyResponse } from '@/types/apiKey';

// ── Static data ───────────────────────────────────────────────────────────────

function buildCodeCurl(base: string): string {
  return `# List your videos
curl -X GET "${base}/videos" \\
  -H "Authorization: Bearer YOUR_API_KEY"

# Get the moderation queue (pending items only)
curl -X GET "${base}/moderation/queue?status=pending" \\
  -H "Authorization: Bearer YOUR_API_KEY"

# Submit a human review decision
curl -X POST "${base}/moderation/{result_id}/review" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"action":"approve","notes":"Content looks clean"}'`;
}

function buildCodePython(base: string): string {
  return `import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "${base}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# List videos
resp = requests.get(f"{BASE_URL}/videos", headers=headers)
resp.raise_for_status()
data = resp.json()
print(f"Found {data['total']} videos")

# Poll the moderation queue
queue = requests.get(
    f"{BASE_URL}/moderation/queue",
    params={"status": "pending", "limit": 20},
    headers=headers,
).json()

for item in queue["items"]:
    print(f"{item['video_title']}: {item['status']}")`;
}

function buildCodeJavascript(base: string): string {
  return `const API_KEY = 'YOUR_API_KEY';
const BASE_URL = '${base}';

const headers = {
  'Authorization': \`Bearer \${API_KEY}\`,
  'Content-Type': 'application/json',
};

// List videos
const videos = await fetch(\`\${BASE_URL}/videos\`, { headers })
  .then((r) => r.json());
console.log(\`Found \${videos.total} videos\`);

// Get the moderation queue
const queue = await fetch(\`\${BASE_URL}/moderation/queue?status=pending\`, { headers })
  .then((r) => r.json());

queue.items.forEach((item) => {
  console.log(\`\${item.video_title}: \${item.status}\`);
});`;
}

function buildCodeGo(base: string): string {
  return `package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func main() {
	const apiKey = "YOUR_API_KEY"
	const baseURL = "${base}"

	req, _ := http.NewRequest("GET", baseURL+"/videos", nil)
	req.Header.Set("Authorization", "Bearer "+apiKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	fmt.Println(result)
}`;
}

const METHOD_COLOURS: Record<string, string> = {
  GET: 'text-green-600 border-green-500/40 bg-green-50 dark:bg-green-950/40',
  POST: 'text-blue-600 border-blue-500/40 bg-blue-50 dark:bg-blue-950/40',
  PUT: 'text-yellow-600 border-yellow-500/40 bg-yellow-50 dark:bg-yellow-950/40',
  PATCH: 'text-orange-600 border-orange-500/40 bg-orange-50 dark:bg-orange-950/40',
  DELETE: 'text-destructive border-destructive/40 bg-destructive/5',
};

interface EndpointDef {
  method: string;
  path: string;
  description: string;
  auth: boolean;
  rateLimit: string;
}

interface EndpointGroup {
  category: string;
  endpoints: EndpointDef[];
}

const ENDPOINT_GROUPS: EndpointGroup[] = [
  {
    category: 'Authentication',
    endpoints: [
      { method: 'POST', path: '/auth/login', description: 'Authenticate with email and password, returns JWT tokens', auth: false, rateLimit: '10/min' },
      { method: 'POST', path: '/auth/refresh', description: 'Exchange a refresh token for a new access token', auth: false, rateLimit: '20/min' },
      { method: 'POST', path: '/auth/logout', description: 'Revoke the current access and refresh tokens', auth: true, rateLimit: '10/min' },
    ],
  },
  {
    category: 'Videos',
    endpoints: [
      { method: 'GET', path: '/videos', description: 'List videos with pagination, status and date filters', auth: true, rateLimit: '120/min' },
      { method: 'GET', path: '/videos/upload-url', description: 'Get a presigned S3 URL for direct file upload', auth: true, rateLimit: '30/min' },
      { method: 'POST', path: '/videos', description: 'Register a video in the system after S3 upload completes', auth: true, rateLimit: '50/min' },
      { method: 'GET', path: '/videos/{id}', description: 'Get video details, metadata, and AI analysis results', auth: true, rateLimit: '120/min' },
      { method: 'DELETE', path: '/videos/{id}', description: 'Soft-delete a video and remove it from analysis queues', auth: true, rateLimit: '20/min' },
    ],
  },
  {
    category: 'Moderation',
    endpoints: [
      { method: 'GET', path: '/moderation/queue', description: 'Retrieve the moderation review queue with status filter', auth: true, rateLimit: '60/min' },
      { method: 'GET', path: '/moderation/videos/{id}', description: 'Get the full moderation report for a specific video', auth: true, rateLimit: '120/min' },
      { method: 'POST', path: '/moderation/{id}/review', description: 'Submit a human review decision (approve/reject/escalate)', auth: true, rateLimit: '20/min' },
      { method: 'DELETE', path: '/moderation/queue/clear', description: 'Clear all approved/rejected items from the queue', auth: true, rateLimit: '5/min' },
    ],
  },
  {
    category: 'Policies',
    endpoints: [
      { method: 'GET', path: '/policies', description: 'List all content moderation policy configurations', auth: true, rateLimit: '60/min' },
      { method: 'POST', path: '/policies', description: 'Create a new moderation policy with rule definitions', auth: true, rateLimit: '10/min' },
      { method: 'PUT', path: '/policies/{id}', description: 'Replace an existing policy configuration entirely', auth: true, rateLimit: '10/min' },
      { method: 'PATCH', path: '/policies/{id}/toggle', description: 'Enable or disable a policy without deleting it', auth: true, rateLimit: '20/min' },
      { method: 'DELETE', path: '/policies/{id}', description: 'Permanently delete a moderation policy', auth: true, rateLimit: '10/min' },
    ],
  },
  {
    category: 'Analytics',
    endpoints: [
      { method: 'GET', path: '/analytics/summary', description: 'Get aggregated video and violation statistics', auth: true, rateLimit: '60/min' },
      { method: 'GET', path: '/analytics/violations', description: 'Get violation trend data with time-range grouping', auth: true, rateLimit: '60/min' },
    ],
  },
  {
    category: 'Live Streams',
    endpoints: [
      { method: 'GET', path: '/live/streams', description: 'List all live monitoring sessions', auth: true, rateLimit: '60/min' },
      { method: 'POST', path: '/live/streams', description: 'Start real-time AI monitoring on a stream URL', auth: true, rateLimit: '10/min' },
      { method: 'GET', path: '/live/streams/{id}', description: 'Get live stream status and real-time analysis events', auth: true, rateLimit: '120/min' },
      { method: 'DELETE', path: '/live/streams/{id}', description: 'Stop monitoring and close the stream session', auth: true, rateLimit: '10/min' },
    ],
  },
  {
    category: 'API Keys',
    endpoints: [
      { method: 'GET', path: '/api-keys', description: 'List all API keys for the authenticated account', auth: true, rateLimit: '20/min' },
      { method: 'POST', path: '/api-keys', description: 'Generate a new named API key (full key shown once)', auth: true, rateLimit: '5/min' },
      { method: 'PATCH', path: '/api-keys/{id}', description: 'Rename an existing API key', auth: true, rateLimit: '10/min' },
      { method: 'DELETE', path: '/api-keys/{id}', description: 'Revoke and permanently delete an API key', auth: true, rateLimit: '10/min' },
    ],
  },
  {
    category: 'Webhooks',
    endpoints: [
      { method: 'POST', path: '/webhooks/{event}', description: 'Receive event notifications at your configured endpoint', auth: false, rateLimit: 'N/A' },
    ],
  },
];

interface SecurityPractice {
  icon: LucideIcon;
  title: string;
  description: string;
  code?: string;
}

const SECURITY_PRACTICES: SecurityPractice[] = [
  {
    icon: Lock,
    title: 'Never commit keys to version control',
    description:
      'Store API keys in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault). Add .env files to .gitignore.',
    code: `# .env.local — add this file to .gitignore
VIDSHIELD_API_KEY=sk_live_your_key_here

# Node.js
const apiKey = process.env.VIDSHIELD_API_KEY;

# Python
import os
api_key = os.environ["VIDSHIELD_API_KEY"]`,
  },
  {
    icon: RefreshCw,
    title: 'Rotate keys regularly',
    description:
      'Generate a replacement key, deploy it to all services, then revoke the old key. Zero-downtime rotation ensures no requests are dropped.',
  },
  {
    icon: Shield,
    title: 'Use separate keys per environment',
    description:
      'Create distinct API keys for development, staging, and production. If a dev key is accidentally exposed, production remains unaffected.',
  },
  {
    icon: ShieldAlert,
    title: 'Revoke compromised keys immediately',
    description:
      'If you suspect a leak, revoke the key from the Keys tab right away. Requests using that key are rejected within seconds of revocation.',
  },
  {
    icon: Zap,
    title: 'Handle rate limits with exponential backoff',
    description:
      'When you receive a 429 Too Many Requests response, wait before retrying. Use the Retry-After header value when available.',
    code: `import time, requests

def api_get(url: str, headers: dict, retries: int = 4) -> dict:
    for attempt in range(retries):
        resp = requests.get(url, headers=headers)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp.json()
        wait = int(resp.headers.get("Retry-After", 2 ** attempt))
        time.sleep(wait)
    raise RuntimeError("Rate limit exceeded after retries")`,
  },
  {
    icon: BookOpen,
    title: 'Always use HTTPS',
    description:
      'All API requests must be made over HTTPS. HTTP connections are rejected. Never pass API keys in URLs or query strings — always use the Authorization header.',
  },
];

// ── CodeBlock ─────────────────────────────────────────────────────────────────

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="relative group">
      <pre className="rounded-md bg-muted p-4 overflow-x-auto text-xs font-mono leading-relaxed whitespace-pre">
        <code>{code}</code>
      </pre>
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleCopy}
        title="Copy code"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-green-500" />
        ) : (
          <Copy className="h-3.5 w-3.5" />
        )}
      </Button>
    </div>
  );
}

// ── Generate Key Dialog ───────────────────────────────────────────────────────

interface GenerateKeyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerated: (result: CreateApiKeyResponse) => void;
}

function GenerateKeyDialog({ open, onOpenChange, onGenerated }: GenerateKeyDialogProps) {
  const [name, setName] = useState('');
  const createKey = useCreateApiKey();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const result = await createKey.mutateAsync({ name: name.trim() });
      setName('');
      onGenerated(result);
      onOpenChange(false);
    } catch {
      // error handled in hook
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Generate new API key</DialogTitle>
          <DialogDescription>
            Give your key a descriptive name so you can identify where it&apos;s used later.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="key-name">Key name</Label>
            <Input
              id="key-name"
              placeholder="e.g. Production server, CI/CD pipeline"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={64}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">Max 64 characters.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name.trim() || createKey.isPending}>
              {createKey.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Generate key
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── New Key Reveal Dialog ─────────────────────────────────────────────────────

function NewKeyRevealDialog({
  apiKey,
  onClose,
}: {
  apiKey: CreateApiKeyResponse | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!apiKey?.key) return;
    await navigator.clipboard.writeText(apiKey.key);
    setCopied(true);
    toast.success('API key copied to clipboard');
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <Dialog open={!!apiKey} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5 text-primary" />
            Your new API key
          </DialogTitle>
          <DialogDescription>
            Copy and store this key securely — it won&apos;t be shown again.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-md border border-yellow-400/50 bg-yellow-50 p-3 dark:bg-yellow-950/30">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-600" />
            <p className="text-sm text-yellow-700 dark:text-yellow-400">
              This is the only time the full key is displayed. Store it in a secrets manager or
              environment variable before closing this dialog.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label>
              Key name:{' '}
              <span className="font-medium text-foreground">{apiKey?.name}</span>
            </Label>
            <div className="flex gap-2">
              <Input
                readOnly
                value={apiKey?.key ?? ''}
                className="font-mono text-xs bg-muted"
              />
              <Button
                variant={copied ? 'default' : 'outline'}
                onClick={handleCopy}
                className="shrink-0"
              >
                {copied ? (
                  <Check className="mr-1.5 h-4 w-4" />
                ) : (
                  <Copy className="mr-1.5 h-4 w-4" />
                )}
                {copied ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onClose} className="w-full sm:w-auto">
            I&apos;ve saved my key — close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Rename Dialog ─────────────────────────────────────────────────────────────

function RenameDialog({ apiKey, onClose }: { apiKey: ApiKey | null; onClose: () => void }) {
  const [name, setName] = useState('');
  const renameKey = useRenameApiKey();

  useEffect(() => {
    setName(apiKey?.name ?? '');
  }, [apiKey?.name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey || !name.trim()) return;
    try {
      await renameKey.mutateAsync({ id: apiKey.id, body: { name: name.trim() } });
      onClose();
    } catch {
      // error handled in hook
    }
  };

  return (
    <Dialog open={!!apiKey} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Rename API key</DialogTitle>
          <DialogDescription>
            Currently:{' '}
            <code className="text-xs font-mono bg-muted px-1 py-0.5 rounded">
              {apiKey?.masked}
            </code>
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new-name">New name</Label>
            <Input
              id="new-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={64}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!name.trim() || name === apiKey?.name || renameKey.isPending}
            >
              {renameKey.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── Revoke Dialog ─────────────────────────────────────────────────────────────

function RevokeDialog({ apiKey, onClose }: { apiKey: ApiKey | null; onClose: () => void }) {
  const revokeKey = useRevokeApiKey();

  const handleRevoke = async () => {
    if (!apiKey) return;
    try {
      await revokeKey.mutateAsync(apiKey.id);
      onClose();
    } catch {
      // error handled in hook
    }
  };

  return (
    <Dialog open={!!apiKey} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-destructive">Revoke API key</DialogTitle>
          <DialogDescription>
            This action is permanent. Any service using this key will lose access immediately.
          </DialogDescription>
        </DialogHeader>
        <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 space-y-0.5">
          <p className="text-sm font-medium">{apiKey?.name}</p>
          <p className="text-xs font-mono text-muted-foreground">{apiKey?.masked}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleRevoke} disabled={revokeKey.isPending}>
            {revokeKey.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Revoke key
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── API Keys Tab ──────────────────────────────────────────────────────────────

function ApiKeysTab({ onGenerateClick }: { onGenerateClick: () => void }) {
  const { data, isLoading } = useApiKeys();
  const [renameTarget, setRenameTarget] = useState<ApiKey | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<ApiKey | null>(null);
  const [search, setSearch] = useState('');

  const items = data?.items ?? [];
  const filtered = search
    ? items.filter((k) => k.name.toLowerCase().includes(search.toLowerCase()))
    : items;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <Input
          placeholder="Search by name…"
          className="w-56"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Button onClick={onGenerateClick} className="ml-auto">
          <Plus className="mr-2 h-4 w-4" />
          Generate new key
        </Button>
      </div>

      {!isLoading && items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <KeyRound className="h-10 w-10 text-muted-foreground mb-3" />
          <h3 className="text-base font-semibold mb-1">No API keys yet</h3>
          <p className="text-sm text-muted-foreground mb-5 max-w-xs">
            Generate your first key to start integrating with the VidShield AI API.
          </p>
          <Button onClick={onGenerateClick}>
            <Plus className="mr-2 h-4 w-4" />
            Generate your first key
          </Button>
        </div>
      )}

      {(isLoading || items.length > 0) && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Last used</TableHead>
                <TableHead className="hidden md:table-cell text-right">Requests (30d)</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 7 }).map((__, j) => (
                        <TableCell key={j}>
                          <Skeleton className="h-4 w-full" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                : filtered.length === 0
                ? (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="text-center py-8 text-sm text-muted-foreground"
                      >
                        No keys match &quot;{search}&quot;
                      </TableCell>
                    </TableRow>
                  )
                : filtered.map((key) => (
                    <TableRow
                      key={key.id}
                      className={key.status === 'revoked' ? 'opacity-50' : ''}
                    >
                      <TableCell className="font-medium">{key.name}</TableCell>
                      <TableCell>
                        <code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">
                          {key.masked}
                        </code>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                        <span title={format(new Date(key.created_at), 'PPpp')}>
                          {formatDistanceToNow(new Date(key.created_at), { addSuffix: true })}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                        {key.last_used_at ? (
                          <span title={format(new Date(key.last_used_at), 'PPpp')}>
                            {formatDistanceToNow(new Date(key.last_used_at), { addSuffix: true })}
                          </span>
                        ) : (
                          <span className="text-muted-foreground/50 text-xs">Never</span>
                        )}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-right">
                        {key.request_count.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={key.status === 'active' ? 'default' : 'secondary'}
                          className="capitalize text-xs"
                        >
                          {key.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {key.status === 'active' && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                                <span className="sr-only">Key actions</span>
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setRenameTarget(key)}>
                                <Pencil className="mr-2 h-4 w-4" />
                                Rename
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive focus:text-destructive"
                                onClick={() => setRevokeTarget(key)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Revoke
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
            </TableBody>
          </Table>
        </div>
      )}

      <RenameDialog apiKey={renameTarget} onClose={() => setRenameTarget(null)} />
      <RevokeDialog apiKey={revokeTarget} onClose={() => setRevokeTarget(null)} />
    </div>
  );
}

// ── Quick Start Tab ───────────────────────────────────────────────────────────

function QuickStartTab({ onGenerateClick }: { onGenerateClick: () => void }) {
  const [lang, setLang] = useState<'curl' | 'python' | 'javascript' | 'go'>('curl');

  const apiRoot = useMemo(() => getBrowserApiV1Root(), []);
  const displayBaseUrl = useMemo(() => {
    if (API_BASE_URL) return API_BASE_URL;
    if (typeof window !== 'undefined') return window.location.origin;
    return '—';
  }, []);

  const codeByLang = useMemo(
    () => ({
      curl: buildCodeCurl(apiRoot),
      python: buildCodePython(apiRoot),
      javascript: buildCodeJavascript(apiRoot),
      go: buildCodeGo(apiRoot),
    }),
    [apiRoot]
  );

  return (
    <div className="space-y-8">
      {/* 3-step guide */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          {
            step: '1',
            icon: KeyRound,
            title: 'Generate an API key',
            description:
              "Create a named API key from the Keys tab. Store it securely — it's shown only once.",
            action: (
              <Button size="sm" onClick={onGenerateClick}>
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Generate key
              </Button>
            ),
          },
          {
            step: '2',
            icon: Code2,
            title: 'Make your first request',
            description:
              'Include the key in the Authorization header. Use the code examples below to call any endpoint.',
            action: null,
          },
          {
            step: '3',
            icon: BookOpen,
            title: 'Explore the reference',
            description:
              'Browse all available endpoints in the Endpoints tab. Each entry lists method, path, and rate limit.',
            action: null,
          },
        ].map(({ step, icon: Icon, title, description, action }) => (
          <Card key={step}>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2 mb-1">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shrink-0">
                  {step}
                </div>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <CardTitle className="text-base">{title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">{description}</p>
              {action}
            </CardContent>
          </Card>
        ))}
      </div>

      <Separator />

      {/* Authentication reference */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Authentication header</CardTitle>
          <CardDescription>Every authenticated request must include this header.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <CodeBlock code="Authorization: Bearer YOUR_API_KEY" />
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            {[
              { label: 'Base URL', value: displayBaseUrl },
              { label: 'API version prefix', value: API_V1 },
              { label: 'Content-Type', value: 'application/json' },
              { label: 'Transport', value: 'HTTPS only' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-md border p-3 space-y-1">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {label}
                </p>
                <code className="text-xs font-mono">{value}</code>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Language-tabbed code examples */}
      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold">Code examples</h2>
          <p className="text-sm text-muted-foreground">
            Replace{' '}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">YOUR_API_KEY</code> with your
            actual API key.
          </p>
        </div>
        <Tabs value={lang} onValueChange={(v) => setLang(v as typeof lang)}>
          <TabsList>
            <TabsTrigger value="curl">cURL</TabsTrigger>
            <TabsTrigger value="python">Python</TabsTrigger>
            <TabsTrigger value="javascript">JavaScript</TabsTrigger>
            <TabsTrigger value="go">Go</TabsTrigger>
          </TabsList>
          {(['curl', 'python', 'javascript', 'go'] as const).map((l) => (
            <TabsContent key={l} value={l} className="mt-3">
              <CodeBlock code={codeByLang[l]} />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      <Separator />

      {/* Error response format */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Error response format</CardTitle>
          <CardDescription>All errors use a consistent JSON envelope.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <CodeBlock
            code={`{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired API key",
    "details": {}
  }
}`}
          />
          <div className="grid gap-2 text-sm sm:grid-cols-2">
            {[
              { status: '400', meaning: 'Bad Request — invalid parameters' },
              { status: '401', meaning: 'Unauthorized — missing or invalid API key' },
              { status: '403', meaning: 'Forbidden — insufficient permissions' },
              { status: '404', meaning: 'Not Found — resource does not exist' },
              { status: '422', meaning: 'Validation Error — request body invalid' },
              { status: '429', meaning: 'Too Many Requests — rate limit exceeded' },
            ].map(({ status, meaning }) => (
              <div key={status} className="flex items-start gap-2 text-xs">
                <Badge variant="outline" className="font-mono shrink-0">
                  {status}
                </Badge>
                <span className="text-muted-foreground">{meaning}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Endpoints Tab ─────────────────────────────────────────────────────────────

function EndpointsTab() {
  const apiRoot = useMemo(() => getBrowserApiV1Root(), []);

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">
        All endpoints use base URL{' '}
        <code className="text-xs bg-muted px-1 py-0.5 rounded">{apiRoot}</code>. Endpoints marked{' '}
        <Badge variant="secondary" className="text-xs">Required</Badge> need an{' '}
        <code className="text-xs bg-muted px-1 py-0.5 rounded">Authorization: Bearer</code> header.
      </p>

      {ENDPOINT_GROUPS.map(({ category, endpoints }) => (
        <Card key={category}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{category}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[90px] pl-6">Method</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead className="hidden sm:table-cell">Description</TableHead>
                  <TableHead className="hidden md:table-cell w-[90px] text-right">Rate limit</TableHead>
                  <TableHead className="w-[90px] pr-6 text-right">Auth</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {endpoints.map((ep) => (
                  <TableRow key={`${ep.method}-${ep.path}`}>
                    <TableCell className="pl-6">
                      <Badge
                        variant="outline"
                        className={`text-xs font-mono font-bold ${METHOD_COLOURS[ep.method] ?? ''}`}
                      >
                        {ep.method}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs font-mono">{ep.path}</code>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                      {ep.description}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-xs text-muted-foreground text-right">
                      {ep.rateLimit}
                    </TableCell>
                    <TableCell className="pr-6 text-right">
                      {ep.auth ? (
                        <Badge variant="secondary" className="text-xs">
                          Required
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs text-muted-foreground">
                          Public
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── Security Tab ──────────────────────────────────────────────────────────────

function SecurityTab() {
  return (
    <div className="space-y-4">
      {SECURITY_PRACTICES.map(({ icon: Icon, title, description, code }) => (
        <Card key={title}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Icon className="h-4 w-4 text-primary shrink-0" />
              {title}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">{description}</p>
            {code && <CodeBlock code={code} />}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ApiKeysPage() {
  const [generateOpen, setGenerateOpen] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState<CreateApiKeyResponse | null>(null);
  const [activeTab, setActiveTab] = useState('keys');

  const openGenerate = () => {
    setActiveTab('keys');
    setGenerateOpen(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
        <p className="text-muted-foreground">
          Manage API credentials and explore the VidShield AI REST API
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="keys" className="flex items-center gap-1.5">
            <KeyRound className="h-3.5 w-3.5" />
            Keys
          </TabsTrigger>
          <TabsTrigger value="quickstart" className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            Quick Start
          </TabsTrigger>
          <TabsTrigger value="endpoints" className="flex items-center gap-1.5">
            <Code2 className="h-3.5 w-3.5" />
            Endpoints
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5" />
            Security
          </TabsTrigger>
        </TabsList>

        <TabsContent value="keys" className="mt-6">
          <ApiKeysTab onGenerateClick={() => setGenerateOpen(true)} />
        </TabsContent>
        <TabsContent value="quickstart" className="mt-6">
          <QuickStartTab onGenerateClick={openGenerate} />
        </TabsContent>
        <TabsContent value="endpoints" className="mt-6">
          <EndpointsTab />
        </TabsContent>
        <TabsContent value="security" className="mt-6">
          <SecurityTab />
        </TabsContent>
      </Tabs>

      <GenerateKeyDialog
        open={generateOpen}
        onOpenChange={setGenerateOpen}
        onGenerated={(result) => setNewKeyResult(result)}
      />
      <NewKeyRevealDialog
        apiKey={newKeyResult}
        onClose={() => setNewKeyResult(null)}
      />
    </div>
  );
}
