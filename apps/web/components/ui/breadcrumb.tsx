'use client';

import * as React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  className?: string;
  separator?: React.ReactNode;
  showHome?: boolean;
  maxItems?: number;
}

// Modern breadcrumb component following accessibility best practices
export function Breadcrumb({
  items = [],
  className,
  separator = <ChevronRight className="h-4 w-4" aria-hidden="true" />,
  showHome = true,
  maxItems = 4,
}: BreadcrumbProps) {
  // Auto-generate breadcrumbs from pathname if no items provided
  const pathname = usePathname();
  const autoItems = React.useMemo(() => {
    if (items.length > 0) return items;

    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Map known routes to readable labels
    const routeLabels: Record<string, string> = {
      dashboard: 'Dashboard',
      tasks: 'Tasks',
      projects: 'Projects',
      calendar: 'Calendar',
      analytics: 'Analytics',
      settings: 'Settings',
      inbox: 'Inbox',
    };

    segments.forEach((segment, index) => {
      const href = `/${segments.slice(0, index + 1).join('/')}`;
      let label = routeLabels[segment] || segment;

      // Handle UUIDs and other complex segments
      if (segment.length > 20 && segment.includes('-')) {
        label = `${segment.slice(0, 8)}...`;
      } else if (!routeLabels[segment]) {
        // Capitalize and format unknown segments
        label = segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
      }

      breadcrumbs.push({
        label,
        href: index === segments.length - 1 ? undefined : href,
      });
    });

    return breadcrumbs;
  }, [items, pathname]);

  // Handle max items with ellipsis
  const displayItems = React.useMemo(() => {
    if (autoItems.length <= maxItems) return autoItems;

    return [
      ...autoItems.slice(0, 1), // First item
      { label: '...', href: undefined }, // Ellipsis
      ...autoItems.slice(-(maxItems - 2)), // Last few items
    ];
  }, [autoItems, maxItems]);

  if (displayItems.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center space-x-1 text-sm text-muted-foreground', className)}
      role="navigation"
    >
      <ol className="flex items-center space-x-1" role="list">
        {/* Home link */}
        {showHome && (
          <>
            <li role="listitem">
              <Link
                href="/dashboard"
                className="flex items-center hover:text-foreground transition-colors"
                aria-label="Go to dashboard"
              >
                <Home className="h-4 w-4" />
                <span className="sr-only">Dashboard</span>
              </Link>
            </li>
            {displayItems.length > 0 && (
              <li role="separator" aria-hidden="true" className="text-muted-foreground/50">
                {separator}
              </li>
            )}
          </>
        )}

        {/* Breadcrumb items */}
        {displayItems.map((item, index) => {
          const isLast = index === displayItems.length - 1;
          const isEllipsis = item.label === '...';

          return (
            <React.Fragment key={`${item.label}-${index}`}>
              <li role="listitem">
                {isEllipsis ? (
                  <span className="text-muted-foreground/70" aria-label="More items">
                    {item.label}
                  </span>
                ) : isLast ? (
                  <span className="font-medium text-foreground" aria-current="page">
                    {item.icon && <item.icon className="h-4 w-4 inline mr-1" />}
                    {item.label}
                  </span>
                ) : (
                  <Link href={item.href!} className="hover:text-foreground transition-colors">
                    {item.icon && <item.icon className="h-4 w-4 inline mr-1" />}
                    {item.label}
                  </Link>
                )}
              </li>

              {/* Separator */}
              {!isLast && (
                <li role="separator" aria-hidden="true" className="text-muted-foreground/50">
                  {separator}
                </li>
              )}
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
}

// Hook for programmatic breadcrumb management
export function useBreadcrumb() {
  const [customItems, setCustomItems] = React.useState<BreadcrumbItem[]>([]);

  const setBreadcrumbs = React.useCallback((items: BreadcrumbItem[]) => {
    setCustomItems(items);
  }, []);

  const addBreadcrumb = React.useCallback((item: BreadcrumbItem) => {
    setCustomItems((prev) => [...prev, item]);
  }, []);

  const clearBreadcrumbs = React.useCallback(() => {
    setCustomItems([]);
  }, []);

  return {
    items: customItems,
    setBreadcrumbs,
    addBreadcrumb,
    clearBreadcrumbs,
  };
}

// Context for sharing breadcrumb state across components
const BreadcrumbContext = React.createContext<{
  items: BreadcrumbItem[];
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
  addBreadcrumb: (item: BreadcrumbItem) => void;
  clearBreadcrumbs: () => void;
} | null>(null);

export function BreadcrumbProvider({ children }: { children: React.ReactNode }) {
  const breadcrumbState = useBreadcrumb();

  return (
    <BreadcrumbContext.Provider value={breadcrumbState}>{children}</BreadcrumbContext.Provider>
  );
}

export function useBreadcrumbContext() {
  const context = React.useContext(BreadcrumbContext);
  if (!context) {
    throw new Error('useBreadcrumbContext must be used within a BreadcrumbProvider');
  }
  return context;
}
