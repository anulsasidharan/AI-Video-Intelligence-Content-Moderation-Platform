'use client';

import { useState } from 'react';
import { Plus, Pencil, Trash2, Lock, ShieldCheck, ShieldOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { PolicyEditor } from '@/components/moderation/PolicyEditor';
import {
  usePolicies,
  useCreatePolicy,
  useUpdatePolicy,
  useDeletePolicy,
  useTogglePolicy,
} from '@/hooks/useModeration';
import { useAuth } from '@/hooks/useAuth';
import type { Policy } from '@/types/moderation';

export default function PoliciesPage() {
  const { isAdmin } = useAuth();
  const { data, isLoading, isError } = usePolicies();
  const { mutate: createPolicy, isPending: creating } = useCreatePolicy();
  const { mutate: updatePolicy, isPending: updating } = useUpdatePolicy();
  const { mutate: deletePolicy } = useDeletePolicy();
  const { mutate: togglePolicy, isPending: toggling } = useTogglePolicy();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null);
  // Track which policy id is being toggled for per-card loading state
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const allPolicies = data?.items ?? [];
  const defaultPolicies = allPolicies.filter((p) => p.is_default);
  const customPolicies = allPolicies.filter((p) => !p.is_default);
  const activeCount = allPolicies.filter((p) => p.is_active).length;

  const openCreate = () => {
    setEditingPolicy(null);
    setDialogOpen(true);
  };

  const openEdit = (policy: Policy) => {
    setEditingPolicy(policy);
    setDialogOpen(true);
  };

  const handleSubmit = (values: Parameters<typeof createPolicy>[0]) => {
    if (editingPolicy) {
      updatePolicy(
        { id: editingPolicy.id, body: values },
        { onSuccess: () => setDialogOpen(false) }
      );
    } else {
      createPolicy(values, { onSuccess: () => setDialogOpen(false) });
    }
  };

  const handleToggle = (policy: Policy) => {
    setTogglingId(policy.id);
    togglePolicy(policy.id, { onSettled: () => setTogglingId(null) });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Skeleton className="h-8 w-40" />
            <Skeleton className="h-4 w-64" />
          </div>
          <Skeleton className="h-9 w-28" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
        <p className="text-sm text-destructive">Failed to load policies.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Policies</h1>
          <p className="text-muted-foreground">
            Configure moderation rules and automated actions
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          New policy
        </Button>
      </div>

      {/* ── Default policies ─────────────────────────────────────────── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Default policies
          </h2>
        </div>
        <p className="text-xs text-muted-foreground">
          Set by your admin and applied to all users. You can enable or disable
          them — you cannot edit or delete them.
        </p>

        {defaultPolicies.length === 0 ? (
          <p className="text-sm italic text-muted-foreground">
            No default policies configured yet.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {defaultPolicies.map((policy) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                isDefault
                canEdit={isAdmin}
                isLastActive={policy.is_active && activeCount === 1}
                isToggling={togglingId === policy.id && toggling}
                onToggle={() => handleToggle(policy)}
                onEdit={() => openEdit(policy)}
                onDelete={() => deletePolicy(policy.id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Custom policies ──────────────────────────────────────────── */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          My policies
        </h2>

        {customPolicies.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-10 text-center">
            <p className="text-sm font-medium">No custom policies</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Default policies are being applied. Create a custom policy to override them.
            </p>
            <Button className="mt-4" size="sm" onClick={openCreate}>
              <Plus className="mr-2 h-3.5 w-3.5" />
              Create policy
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {customPolicies.map((policy) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                isDefault={false}
                canEdit
                isLastActive={policy.is_active && activeCount === 1}
                isToggling={togglingId === policy.id && toggling}
                onToggle={() => handleToggle(policy)}
                onEdit={() => openEdit(policy)}
                onDelete={() => deletePolicy(policy.id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Create / Edit dialog ─────────────────────────────────────── */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingPolicy ? 'Edit policy' : 'Create policy'}
            </DialogTitle>
          </DialogHeader>
          <PolicyEditor
            policy={editingPolicy ?? undefined}
            isAdmin={isAdmin}
            onSubmit={handleSubmit}
            onCancel={() => setDialogOpen(false)}
            isSubmitting={creating || updating}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── PolicyCard ──────────────────────────────────────────────────────────────

interface PolicyCardProps {
  policy: Policy;
  isDefault: boolean;
  canEdit: boolean;
  isLastActive: boolean;
  isToggling: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function PolicyCard({
  policy,
  isDefault,
  canEdit,
  isLastActive,
  isToggling,
  onToggle,
  onEdit,
  onDelete,
}: PolicyCardProps) {
  const ruleCount = (policy.rules ?? []).length;
  const toggleDisabled = isToggling || isLastActive;

  return (
    <Card className={policy.is_active ? '' : 'opacity-60'}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          {/* Title + lock icon for default policies */}
          <div className="flex min-w-0 items-center gap-1.5">
            {isDefault && (
              <Lock
                className="h-3.5 w-3.5 shrink-0 text-muted-foreground"
                aria-label="Default policy"
              />
            )}
            <CardTitle className="truncate text-base">{policy.name}</CardTitle>
          </div>

          {/* Enable / Disable toggle — present on every card */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                {/* span wrapper needed so Tooltip works on a disabled element */}
                <span className="shrink-0">
                  <Switch
                    checked={policy.is_active}
                    onCheckedChange={onToggle}
                    disabled={toggleDisabled}
                    aria-label={policy.is_active ? 'Disable policy' : 'Enable policy'}
                  />
                </span>
              </TooltipTrigger>
              {isLastActive && (
                <TooltipContent side="top">
                  At least one policy must remain active
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>
        </div>

        {policy.description && (
          <CardDescription className="text-xs">{policy.description}</CardDescription>
        )}
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Status + type badges */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={policy.is_active ? 'success' : 'secondary'} className="text-xs">
            {policy.is_active ? (
              <><ShieldCheck className="mr-1 h-3 w-3" />Active</>
            ) : (
              <><ShieldOff className="mr-1 h-3 w-3" />Inactive</>
            )}
          </Badge>
          {isDefault && (
            <Badge variant="outline" className="text-xs">
              Default
            </Badge>
          )}
        </div>

        {/* Rules summary */}
        <p className="text-xs text-muted-foreground">
          {ruleCount} rule{ruleCount !== 1 ? 's' : ''}&nbsp;&middot;&nbsp;
          Default action:&nbsp;<strong>{policy.default_action}</strong>
        </p>

        {/* Edit / Delete — only when the caller grants canEdit */}
        {canEdit && (
          <div className="flex justify-end gap-1 pt-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onEdit}
              aria-label="Edit policy"
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
            {/* Delete is hidden for default policies regardless of canEdit */}
            {!isDefault && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={onDelete}
                aria-label="Delete policy"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
