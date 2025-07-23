'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface DashboardGridProps {
  children: React.ReactNode;
  className?: string;
}

export function DashboardGrid({ children, className }: DashboardGridProps) {
  return (
    <div
      className={cn(
        'grid gap-4 auto-rows-min',
        'grid-cols-1',
        'sm:grid-cols-2',
        'lg:grid-cols-3',
        'xl:grid-cols-4',
        className
      )}
    >
      {children}
    </div>
  );
}

interface GridItemProps {
  children: React.ReactNode;
  className?: string;
  colSpan?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  rowSpan?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

export function GridItem({
  children,
  className,
  colSpan = { default: 1 },
  rowSpan = { default: 1 },
}: GridItemProps) {
  const colSpanClasses = [
    colSpan.default && `col-span-${colSpan.default}`,
    colSpan.sm && `sm:col-span-${colSpan.sm}`,
    colSpan.md && `md:col-span-${colSpan.md}`,
    colSpan.lg && `lg:col-span-${colSpan.lg}`,
    colSpan.xl && `xl:col-span-${colSpan.xl}`,
  ].filter(Boolean);

  const rowSpanClasses = [
    rowSpan.default && `row-span-${rowSpan.default}`,
    rowSpan.sm && `sm:row-span-${rowSpan.sm}`,
    rowSpan.md && `md:row-span-${rowSpan.md}`,
    rowSpan.lg && `lg:row-span-${rowSpan.lg}`,
    rowSpan.xl && `xl:row-span-${rowSpan.xl}`,
  ].filter(Boolean);

  return <div className={cn([...colSpanClasses, ...rowSpanClasses], className)}>{children}</div>;
}

// Predefined layouts for common dashboard patterns
export function KPIGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">{children}</div>;
}

export function ChartGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">{children}</div>;
}

export function MainChart({ children }: { children: React.ReactNode }) {
  return <div className="col-span-full">{children}</div>;
}

// Dashboard layout components
export function DashboardHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between space-y-2">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
        {description && <p className="text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex items-center space-x-2">{actions}</div>}
    </div>
  );
}

export function DashboardSection({
  title,
  description,
  children,
  className,
}: {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn('space-y-4', className)}>
      {title && (
        <div className="space-y-1">
          <h3 className="text-lg font-medium">{title}</h3>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      )}
      {children}
    </section>
  );
}

// Responsive breakpoints helper
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// Grid size utilities
export const gridSizes = {
  kpi: {
    mobile: 'grid-cols-1',
    tablet: 'sm:grid-cols-2',
    desktop: 'lg:grid-cols-4',
  },
  charts: {
    mobile: 'grid-cols-1',
    desktop: 'lg:grid-cols-2',
  },
  full: 'col-span-full',
} as const;
