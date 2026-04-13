'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  ContactRound,
  CreditCard,
  FileText,
  Film,
  Headphones,
  KeyRound,
  Radio,
  ScrollText,
  Settings,
  Shield,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Upload,
  Users,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/constants';
import { useAuth } from '@/hooks/useAuth';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
  tourId?: string;
}

const navItems: NavItem[] = [
  { label: 'Overview', href: ROUTES.dashboard, icon: BarChart3, tourId: 'nav-overview' },
  { label: 'Videos', href: ROUTES.videos, icon: Film },
  { label: 'Upload', href: ROUTES.videoUpload, icon: Upload, tourId: 'nav-upload' },
  { label: 'Moderation Queue', href: ROUTES.moderationQueue, icon: ShieldAlert, tourId: 'nav-moderation' },
  { label: 'Policies', href: ROUTES.moderationPolicies, icon: Shield },
  { label: 'Live Streams', href: ROUTES.live, icon: Radio, tourId: 'nav-live' },
  { label: 'API Keys', href: ROUTES.apiKeys, icon: KeyRound },
  { label: 'Billing', href: ROUTES.billing, icon: CreditCard },
  { label: 'Upgrade Plan', href: ROUTES.pricing, icon: Sparkles },
  { label: 'Reports', href: ROUTES.reports, icon: FileText, adminOnly: true, tourId: 'nav-reports' },
  { label: 'User Management', href: ROUTES.userManagement, icon: Users, adminOnly: true },
  { label: 'Explainability & Audit Trail', href: ROUTES.auditTrail, icon: ScrollText, adminOnly: true },
  { label: 'Revenue', href: ROUTES.adminRevenue, icon: TrendingUp, adminOnly: true },
  { label: 'Subscribers', href: ROUTES.adminSubscribers, icon: ContactRound, adminOnly: true },
  { label: 'Support Tickets', href: ROUTES.supportTickets, icon: Headphones, adminOnly: true },
];

const bottomNavItems: NavItem[] = [
  { label: 'Settings', href: ROUTES.settings, icon: Settings, tourId: 'nav-settings' },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const { isAdmin } = useAuth();

  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside
      className={cn(
        'flex h-full w-60 flex-col bg-sidebar text-sidebar-foreground',
        className
      )}
    >
      {/* Logo — click to go home */}
      <Link
        href={ROUTES.dashboard}
        className="flex h-16 items-center gap-2 px-6 hover:opacity-80 transition-opacity"
        aria-label="Go to dashboard home"
      >
        <Shield className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold tracking-tight">VidShield AI</span>
      </Link>

      <Separator className="bg-sidebar-border" />

      {/* Main nav */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav aria-label="Main navigation">
          <ul className="space-y-1">
            {visibleItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  data-tour={item.tourId}
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
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </ScrollArea>

      <Separator className="bg-sidebar-border" />

      {/* Bottom nav */}
      <nav className="px-3 py-4" aria-label="Settings navigation">
        <ul className="space-y-1">
          {bottomNavItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                data-tour={item.tourId}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  pathname === item.href
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
