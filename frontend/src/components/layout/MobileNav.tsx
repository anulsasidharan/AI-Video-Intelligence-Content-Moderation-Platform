'use client';

import { useState } from 'react';
import Link, { type LinkProps } from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  BarChart3,
  ContactRound,
  CreditCard,
  FileText,
  Film,
  Headphones,
  KeyRound,
  Menu,
  Radio,
  ScrollText,
  Settings,
  Shield,
  ShieldAlert,
  TrendingUp,
  Upload,
  Users,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';

const navItems = [
  { label: 'Overview', href: ROUTES.dashboard, icon: BarChart3, adminOnly: false },
  { label: 'Videos', href: ROUTES.videos, icon: Film, adminOnly: false },
  { label: 'Upload', href: ROUTES.videoUpload, icon: Upload, adminOnly: false },
  { label: 'Moderation Queue', href: ROUTES.moderationQueue, icon: ShieldAlert, adminOnly: false },
  { label: 'Policies', href: ROUTES.moderationPolicies, icon: Shield, adminOnly: false },
  { label: 'Live Streams', href: ROUTES.live, icon: Radio, adminOnly: false },
  { label: 'API Keys', href: ROUTES.apiKeys, icon: KeyRound, adminOnly: false },
  { label: 'Billing', href: ROUTES.billing, icon: CreditCard, adminOnly: false },
  { label: 'Reports', href: ROUTES.reports, icon: FileText, adminOnly: true },
  { label: 'User Management', href: ROUTES.userManagement, icon: Users, adminOnly: true },
  { label: 'Explainability & Audit Trail', href: ROUTES.auditTrail, icon: ScrollText, adminOnly: true },
  { label: 'Revenue', href: ROUTES.adminRevenue, icon: TrendingUp, adminOnly: true },
  { label: 'Subscribers', href: ROUTES.adminSubscribers, icon: ContactRound, adminOnly: true },
  { label: 'Support Tickets', href: ROUTES.supportTickets, icon: Headphones, adminOnly: true },
  { label: 'Settings', href: ROUTES.settings, icon: Settings, adminOnly: false },
];

interface MobileLinkProps extends LinkProps {
  children: React.ReactNode;
  className?: string;
  onOpenChange: (open: boolean) => void;
}

function MobileLink({ href, onOpenChange, children, className, ...props }: MobileLinkProps) {
  const router = useRouter();
  return (
    <Link
      href={href}
      onClick={() => {
        router.push(href.toString());
        onOpenChange(false);
      }}
      className={cn('text-sidebar-foreground/80 hover:text-sidebar-foreground', className)}
      {...props}
    >
      {children}
    </Link>
  );
}

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { isAdmin } = useAuth();
  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation menu">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent>
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 px-6 pr-10">
          <Shield className="h-5 w-5 text-primary shrink-0" />
          <SheetTitle className="text-base font-semibold tracking-tight">VidShield AI</SheetTitle>
        </div>

        <Separator className="bg-sidebar-border" />

        <ScrollArea className="flex-1 px-3 py-4 h-[calc(100vh-5rem)]">
          <nav aria-label="Mobile navigation">
            <ul className="space-y-1">
              {visibleItems.map((item) => (
                <li key={item.href}>
                  <MobileLink
                    href={item.href}
                    onOpenChange={setOpen}
                    className={cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      pathname === item.href || pathname.startsWith(item.href + '/')
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                    )}
                    aria-current={pathname === item.href ? 'page' : undefined}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </MobileLink>
                </li>
              ))}
            </ul>
          </nav>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
