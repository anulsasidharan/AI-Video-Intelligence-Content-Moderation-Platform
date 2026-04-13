'use client';

import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { VIOLATION_CATEGORY_LABELS } from '@/lib/constants';
import type { Policy, ViolationCategory, PolicyAction } from '@/types/moderation';

const CATEGORIES: ViolationCategory[] = [
  'violence', 'nudity', 'drugs', 'hate_symbols', 'spam', 'misinformation', 'other',
];
const ACTIONS: PolicyAction[] = ['block', 'flag', 'allow'];
const ACTION_LABELS: Record<PolicyAction, string> = {
  block: 'Block',
  flag: 'Flag',
  allow: 'Allow',
};

const ruleSchema = z.object({
  category: z.enum(['violence', 'nudity', 'drugs', 'hate_symbols', 'spam', 'misinformation', 'other']),
  threshold: z.number().min(0).max(1),
  action: z.enum(['block', 'flag', 'allow']),
});

const policySchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().max(500).optional(),
  rules: z.array(ruleSchema),
  default_action: z.enum(['block', 'flag', 'allow']),
  is_active: z.boolean(),
  is_default: z.boolean(),
});

type PolicyFormValues = z.infer<typeof policySchema>;

interface PolicyEditorProps {
  policy?: Policy;
  isAdmin?: boolean;
  onSubmit: (values: PolicyFormValues) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function PolicyEditor({ policy, isAdmin = false, onSubmit, onCancel, isSubmitting }: PolicyEditorProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<PolicyFormValues>({
    resolver: zodResolver(policySchema),
    defaultValues: policy
      ? {
          name: policy.name,
          description: policy.description ?? '',
          rules: (policy.rules ?? []) as PolicyFormValues['rules'],
          default_action: (policy.default_action ?? 'flag') as PolicyAction,
          is_active: policy.is_active,
          is_default: policy.is_default,
        }
      : {
          name: '',
          description: '',
          rules: [],
          default_action: 'flag',
          is_active: true,
          is_default: false,
        },
  });

  const { fields: ruleFields, append: appendRule, remove: removeRule } = useFieldArray({
    control,
    name: 'rules',
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Name & description */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Policy name</Label>
          <Input id="name" placeholder="e.g. Strict Violence Policy" {...register('name')} />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="description">Description (optional)</Label>
          <Textarea id="description" placeholder="Describe this policy…" rows={2} {...register('description')} />
        </div>
      </div>

      <Separator />

      {/* Rules */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Rules</h3>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => appendRule({ category: 'violence', threshold: 0.7, action: 'flag' })}
          >
            <Plus className="mr-1 h-3 w-3" />
            Add rule
          </Button>
        </div>

        {ruleFields.length === 0 && (
          <p className="text-xs text-muted-foreground">No rules yet. Add a rule to define thresholds per category.</p>
        )}

        <div className="space-y-3">
          {ruleFields.map((field, index) => (
            <div key={field.id} className="flex items-end gap-2 rounded-md border p-3">
              <div className="flex-1 space-y-1">
                <Label className="text-xs">Category</Label>
                <Controller
                  control={control}
                  name={`rules.${index}.category`}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map((cat) => (
                          <SelectItem key={cat} value={cat} className="text-xs">
                            {VIOLATION_CATEGORY_LABELS[cat]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="w-28 space-y-1">
                <Label className="text-xs">Threshold (0–1)</Label>
                <Input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  className="h-8 text-xs"
                  {...register(`rules.${index}.threshold`, { valueAsNumber: true })}
                />
              </div>
              <div className="flex-1 space-y-1">
                <Label className="text-xs">Action</Label>
                <Controller
                  control={control}
                  name={`rules.${index}.action`}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ACTIONS.map((a) => (
                          <SelectItem key={a} value={a} className="text-xs">
                            {ACTION_LABELS[a]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0"
                onClick={() => removeRule(index)}
                aria-label="Remove rule"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Default action */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Default action</h3>
        <p className="text-xs text-muted-foreground">Applied to content that does not match any rule.</p>
        <Controller
          control={control}
          name="default_action"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTIONS.map((a) => (
                  <SelectItem key={a} value={a}>
                    {ACTION_LABELS[a]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <Separator />

      {/* Active toggle */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium">Active</p>
          <p className="text-xs text-muted-foreground">
            Inactive policies are saved but not applied during moderation
          </p>
        </div>
        <Controller
          control={control}
          name="is_active"
          render={({ field }) => (
            <Switch checked={field.value} onCheckedChange={field.onChange} />
          )}
        />
      </div>

      {/* Default policy toggle — admin only */}
      {isAdmin && (
        <div className="flex items-center justify-between rounded-md border border-dashed p-3">
          <div>
            <p className="text-sm font-medium">Default policy</p>
            <p className="text-xs text-muted-foreground">
              Default policies are visible to all users and applied as a
              fallback when no custom policy exists
            </p>
          </div>
          <Controller
            control={control}
            name="is_default"
            render={({ field }) => (
              <Switch checked={field.value} onCheckedChange={field.onChange} />
            )}
          />
        </div>
      )}

      {/* Submit */}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : policy ? 'Save changes' : 'Create policy'}
        </Button>
      </div>
    </form>
  );
}
