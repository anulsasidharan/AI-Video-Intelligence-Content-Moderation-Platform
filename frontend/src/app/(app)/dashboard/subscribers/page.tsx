'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ChevronLeft, ChevronRight, Mail } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { ROUTES } from '@/lib/constants';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { SubscriberListResponse } from '@/types/billing';

const PAGE_SIZE = 50;

export default function AdminSubscribersPage() {
  const router = useRouter();
  const { isAdmin, user } = useAuth();
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (user && !isAdmin) {
      router.replace(ROUTES.dashboard);
    }
  }, [isAdmin, user, router]);

  const q = useQuery({
    queryKey: ['admin', 'billing', 'subscribers', page],
    queryFn: () =>
      apiClient.get<SubscriberListResponse>(
        `/admin/billing/subscribers?page=${page}&page_size=${PAGE_SIZE}`
      ),
    enabled: !!user && isAdmin,
  });

  const totalPages = q.data ? Math.max(1, Math.ceil(q.data.total / q.data.page_size)) : 1;

  if (user && !isAdmin) {
    return (
      <div className="flex h-48 items-center justify-center text-muted-foreground text-sm">
        Redirecting…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Subscribers</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Registered accounts and newsletter signups (&quot;Stay in the loop&quot;), deduplicated by email.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-start gap-3 space-y-0">
          <div className="rounded-lg border bg-muted/40 p-2">
            <Mail className="h-5 w-5 text-primary" />
          </div>
          <div className="space-y-1">
            <CardTitle className="text-base">Audience</CardTitle>
            <CardDescription>
              {q.data != null ? (
                <>
                  Showing {q.data.items.length} of {q.data.total} contacts
                </>
              ) : (
                'Loading…'
              )}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {q.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : q.isError ? (
            <p className="text-sm text-destructive">Could not load subscribers.</p>
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Since</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {q.data!.items.map((row) => (
                      <TableRow key={`${row.source}-${row.email}-${row.user_id ?? 'nl'}`}>
                        <TableCell className="font-medium">{row.email}</TableCell>
                        <TableCell className="text-muted-foreground">{row.name ?? '—'}</TableCell>
                        <TableCell>
                          {row.role ? (
                            <Badge variant="outline" className="text-xs capitalize">
                              {row.role}
                            </Badge>
                          ) : (
                            '—'
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={row.source === 'account' ? 'default' : 'secondary'}>
                            {row.source === 'account' ? 'Account' : 'Newsletter'}
                          </Badge>
                        </TableCell>
                        <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                          {format(new Date(row.created_at), 'PP')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  Page {page} of {totalPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
