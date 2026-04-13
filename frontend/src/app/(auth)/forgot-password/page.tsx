'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Shield, ArrowLeft, Mail } from 'lucide-react';
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

const forgotPasswordSchema = z.object({
  email: z.string().email('Enter a valid email address'),
});

type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (values: ForgotPasswordValues) => {
    setIsLoading(true);
    try {
      await apiClient.post('/auth/forgot-password', { email: values.email });
      setSubmitted(true);
    } catch {
      // The API always returns 200 — this only fires on network errors
      toast.error('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
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
          {submitted ? (
            <>
              <CardHeader className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                  <Mail className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Check your email</CardTitle>
                <CardDescription>
                  If an account with that email exists, we&apos;ve sent a password reset link.
                  The link expires in 30 minutes.
                </CardDescription>
              </CardHeader>
              <CardFooter className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground">
                  Didn&apos;t receive an email? Check your spam folder or{' '}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => setSubmitted(false)}
                  >
                    try again
                  </button>
                  .
                </p>
                <Link
                  href={ROUTES.login}
                  className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary hover:underline"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Back to sign in
                </Link>
              </CardFooter>
            </>
          ) : (
            <>
              <CardHeader>
                <CardTitle>Forgot password?</CardTitle>
                <CardDescription>
                  Enter your email address and we&apos;ll send you a link to reset your password.
                </CardDescription>
              </CardHeader>

              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@example.com"
                      autoComplete="email"
                      {...register('email')}
                      aria-invalid={!!errors.email}
                    />
                    {errors.email && (
                      <p className="text-xs text-destructive" role="alert">
                        {errors.email.message}
                      </p>
                    )}
                  </div>
                </CardContent>

                <CardFooter className="flex flex-col gap-3">
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? 'Sending…' : 'Send reset link'}
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
