'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Shield, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { ROUTES } from '@/lib/constants';

const resetPasswordSchema = z
  .object({
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one digit'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMessage('No reset token found. Please request a new password reset link.');
    }
  }, [token]);

  const onSubmit = async (values: ResetPasswordValues) => {
    if (!token) return;

    setStatus('loading');
    try {
      await apiClient.post('/auth/reset-password', {
        token,
        new_password: values.new_password,
      });
      setStatus('success');
      toast.success('Password reset successfully!');
      setTimeout(() => router.push(ROUTES.login), 3000);
    } catch (err: unknown) {
      setStatus('error');
      const msg =
        (err as { response?: { data?: { detail?: string; error?: { message?: string } } } })
          ?.response?.data?.error?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Invalid or expired reset link. Please request a new one.';
      setErrorMessage(msg);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold tracking-tight">VidShield AI</span>
          </div>
          <p className="text-sm text-muted-foreground">
            AI Video Intelligence &amp; Content Moderation
          </p>
        </div>

        <Card>
          {status === 'success' && (
            <>
              <CardHeader className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                  <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <CardTitle>Password reset!</CardTitle>
                <CardDescription>
                  Your password has been reset successfully. You will be redirected to sign in
                  shortly.
                </CardDescription>
              </CardHeader>
              <CardFooter>
                <Link href={ROUTES.login} className="w-full">
                  <Button className="w-full">Sign in now</Button>
                </Link>
              </CardFooter>
            </>
          )}

          {status === 'error' && (
            <>
              <CardHeader className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                  <AlertCircle className="h-6 w-6 text-destructive" />
                </div>
                <CardTitle>Link invalid or expired</CardTitle>
                <CardDescription>{errorMessage}</CardDescription>
              </CardHeader>
              <CardFooter className="flex flex-col gap-3">
                <Link href={ROUTES.forgotPassword} className="w-full">
                  <Button className="w-full">Request new reset link</Button>
                </Link>
                <Link
                  href={ROUTES.login}
                  className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary hover:underline"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to sign in
                </Link>
              </CardFooter>
            </>
          )}

          {(status === 'idle' || status === 'loading') && token && (
            <>
              <CardHeader>
                <CardTitle>Set new password</CardTitle>
                <CardDescription>
                  Enter your new password below. It must be at least 8 characters and include
                  uppercase, lowercase, and a number.
                </CardDescription>
              </CardHeader>

              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="new_password">New password</Label>
                    <Input
                      id="new_password"
                      type="password"
                      placeholder="••••••••"
                      autoComplete="new-password"
                      {...register('new_password')}
                      aria-invalid={!!errors.new_password}
                    />
                    {errors.new_password && (
                      <p className="text-xs text-destructive" role="alert">
                        {errors.new_password.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm new password</Label>
                    <Input
                      id="confirm_password"
                      type="password"
                      placeholder="••••••••"
                      autoComplete="new-password"
                      {...register('confirm_password')}
                      aria-invalid={!!errors.confirm_password}
                    />
                    {errors.confirm_password && (
                      <p className="text-xs text-destructive" role="alert">
                        {errors.confirm_password.message}
                      </p>
                    )}
                  </div>
                </CardContent>

                <CardFooter className="flex flex-col gap-3">
                  <Button type="submit" className="w-full" disabled={status === 'loading'}>
                    {status === 'loading' ? 'Resetting…' : 'Reset password'}
                  </Button>
                  <Link
                    href={ROUTES.login}
                    className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary hover:underline"
                  >
                    <ArrowLeft className="h-3 w-3" />
                    Back to sign in
                  </Link>
                </CardFooter>
              </form>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
