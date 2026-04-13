'use client';

import { useTheme } from 'next-themes';
import { Monitor, Moon, Sun } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import type { User } from '@/types/user';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';

// ── Schemas ───────────────────────────────────────────────────────────────────

const E164_RE = /^\+[1-9]\d{6,14}$/;

const editProfileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(255),
  whatsapp_number: z
    .string()
    .regex(E164_RE, 'Enter a valid WhatsApp number in E.164 format, e.g. +919876543210')
    .or(z.literal(''))
    .optional(),
  address_line1: z.string().max(255).optional(),
  address_line2: z.string().max(255).optional(),
  city: z.string().max(128).optional(),
  state: z.string().max(128).optional(),
  postal_code: z.string().max(32).optional(),
  country: z.string().max(128).optional(),
});

const changePasswordSchema = z.object({
  current_password: z.string().min(1, 'Enter your current password'),
  new_password: z.string().min(8, 'New password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});

type EditProfileForm = z.infer<typeof editProfileSchema>;
type ChangePasswordForm = z.infer<typeof changePasswordSchema>;

// ── Profile page ──────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const { user, logout, setUser } = useAuth();
  const { theme, setTheme } = useTheme();

  // ── Edit profile form ──────────────────────────────────────────────────────
  const {
    register: regProfile,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors },
  } = useForm<EditProfileForm>({
    resolver: zodResolver(editProfileSchema),
    values: {
      name: user?.name ?? '',
      whatsapp_number: user?.whatsapp_number ?? '',
      address_line1: user?.address_line1 ?? '',
      address_line2: user?.address_line2 ?? '',
      city: user?.city ?? '',
      state: user?.state ?? '',
      postal_code: user?.postal_code ?? '',
      country: user?.country ?? '',
    },
  });

  const { mutate: saveProfile, isPending: savingProfile } = useMutation({
    mutationFn: (body: EditProfileForm) => {
      // Send only non-empty strings; empty string means "no change requested"
      const payload: Record<string, string> = {};
      (Object.keys(body) as (keyof EditProfileForm)[]).forEach((k) => {
        const v = body[k];
        if (v !== undefined && v !== '') payload[k] = v;
      });
      return apiClient.patch<User>('/users/me/profile', payload);
    },
    onSuccess: (updated) => {
      setUser(updated);
      toast.success('Profile updated successfully');
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message ?? 'Failed to update profile';
      toast.error(msg);
    },
  });

  // ── Change password form ───────────────────────────────────────────────────
  const {
    register: regPw,
    handleSubmit: handlePwSubmit,
    reset: resetPw,
    formState: { errors: pwErrors },
  } = useForm<ChangePasswordForm>({ resolver: zodResolver(changePasswordSchema) });

  const { mutate: changePassword, isPending: changingPassword } = useMutation({
    mutationFn: ({ current_password, new_password }: ChangePasswordForm) =>
      apiClient.patch('/users/me/password', { current_password, new_password }),
    onSuccess: () => {
      toast.success('Password changed successfully');
      resetPw();
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message ?? 'Failed to change password';
      toast.error(msg);
    },
  });

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const themes = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Monitor },
  ] as const;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground">Your account information and preferences</p>
      </div>

      {/* ── Account info (read-only summary) ────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Your personal details and role</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-5">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-xl">{initials}</AvatarFallback>
            </Avatar>
            <div className="space-y-1">
              <p className="text-lg font-semibold">{user?.name}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <Badge variant="secondary" className="capitalize">
                {user?.role === 'api_consumer' ? 'API Consumer' : user?.role}
              </Badge>
            </div>
          </div>

          <Separator />

          <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <div className="space-y-1">
              <dt className="text-muted-foreground">User ID</dt>
              <dd className="font-mono text-xs break-all">{user?.id ?? '—'}</dd>
            </div>
            <div className="space-y-1">
              <dt className="text-muted-foreground">Organization</dt>
              <dd>{user?.organization_id ?? '—'}</dd>
            </div>
            <div className="space-y-1">
              <dt className="text-muted-foreground">WhatsApp</dt>
              <dd>{user?.whatsapp_number ?? '—'}</dd>
            </div>
            <div className="space-y-1">
              <dt className="text-muted-foreground">Member since</dt>
              <dd>
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })
                  : '—'}
              </dd>
            </div>
            {(user?.city || user?.country) && (
              <div className="space-y-1 sm:col-span-2">
                <dt className="text-muted-foreground">Address</dt>
                <dd className="text-sm">
                  {[user.address_line1, user.address_line2, user.city, user.state, user.postal_code, user.country]
                    .filter(Boolean)
                    .join(', ')}
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* ── Edit Profile ────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Edit Profile</CardTitle>
          <CardDescription>Update your name, WhatsApp number, and address</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit((v) => saveProfile(v))} className="space-y-5">
            {/* Name */}
            <div className="space-y-1.5">
              <Label htmlFor="prof-name">Full name</Label>
              <Input id="prof-name" placeholder="Jane Smith" {...regProfile('name')} />
              {profileErrors.name && (
                <p className="text-xs text-destructive">{profileErrors.name.message}</p>
              )}
            </div>

            {/* WhatsApp */}
            <div className="space-y-1.5">
              <Label htmlFor="prof-whatsapp">
                WhatsApp number
                <span className="ml-1 text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="prof-whatsapp"
                type="tel"
                placeholder="+919876543210"
                {...regProfile('whatsapp_number')}
              />
              <p className="text-xs text-muted-foreground">
                International format with country code, e.g. +1 for US, +91 for India
              </p>
              {profileErrors.whatsapp_number && (
                <p className="text-xs text-destructive">{profileErrors.whatsapp_number.message}</p>
              )}
            </div>

            <Separator />

            {/* Address */}
            <p className="text-sm font-medium">Address</p>

            <div className="space-y-1.5">
              <Label htmlFor="addr1">Address line 1</Label>
              <Input id="addr1" placeholder="123 Main Street" {...regProfile('address_line1')} />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="addr2">
                Address line 2
                <span className="ml-1 text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Input id="addr2" placeholder="Apt 4B" {...regProfile('address_line2')} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="city">City</Label>
                <Input id="city" placeholder="Mumbai" {...regProfile('city')} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="state">State / Province</Label>
                <Input id="state" placeholder="Maharashtra" {...regProfile('state')} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="postal_code">Postal code</Label>
                <Input id="postal_code" placeholder="400001" {...regProfile('postal_code')} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="country">Country</Label>
                <Input id="country" placeholder="India" {...regProfile('country')} />
              </div>
            </div>

            <Button type="submit" disabled={savingProfile}>
              {savingProfile ? 'Saving…' : 'Save profile'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* ── Appearance ──────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how VidShield AI looks for you</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            {themes.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors hover:bg-accent ${
                  theme === value ? 'border-primary bg-accent' : 'border-border'
                }`}
                aria-pressed={theme === value}
              >
                <Icon className="h-5 w-5" />
                <span className="text-sm font-medium">{label}</span>
                {value === 'system' && (
                  <span className="text-[10px] text-muted-foreground">Follows OS</span>
                )}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            <strong>System</strong> mode automatically follows your operating system&apos;s
            light/dark preference — recommended for eye comfort.
          </p>
        </CardContent>
      </Card>

      {/* ── Change Password ──────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePwSubmit((v) => changePassword(v))} className="space-y-4 max-w-sm">
            <div className="space-y-1.5">
              <Label htmlFor="current_password">Current password</Label>
              <Input
                id="current_password"
                type="password"
                placeholder="••••••••"
                {...regPw('current_password')}
              />
              {pwErrors.current_password && (
                <p className="text-xs text-destructive">{pwErrors.current_password.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new_password">New password</Label>
              <Input
                id="new_password"
                type="password"
                placeholder="••••••••"
                {...regPw('new_password')}
              />
              {pwErrors.new_password && (
                <p className="text-xs text-destructive">{pwErrors.new_password.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm_password">Confirm new password</Label>
              <Input
                id="confirm_password"
                type="password"
                placeholder="••••••••"
                {...regPw('confirm_password')}
              />
              {pwErrors.confirm_password && (
                <p className="text-xs text-destructive">{pwErrors.confirm_password.message}</p>
              )}
            </div>
            <Button type="submit" disabled={changingPassword}>
              {changingPassword ? 'Saving…' : 'Update password'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* ── Session ──────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
          <CardDescription>Manage your current session</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Active session</p>
              <p className="text-xs text-muted-foreground">You are currently signed in</p>
            </div>
            <Button variant="destructive" size="sm" onClick={logout}>
              Sign out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
