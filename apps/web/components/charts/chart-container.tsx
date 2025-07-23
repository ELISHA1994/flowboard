'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface ChartContainerProps {
  title: string;
  description?: string;
  className?: string;
  children: React.ReactNode;
  isLoading?: boolean;
  error?: Error | null;
  actions?: React.ReactNode;
}

export function ChartContainer({
  title,
  description,
  className,
  children,
  isLoading = false,
  error = null,
  actions,
}: ChartContainerProps) {
  return (
    <Card className={cn('h-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-base font-medium">{title}</CardTitle>
          {description && (
            <CardDescription className="text-xs text-muted-foreground">
              {description}
            </CardDescription>
          )}
        </div>
        {actions}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[200px] items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex h-[200px] items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Failed to load chart data</p>
              <p className="text-xs text-muted-foreground mt-1">{error.message}</p>
            </div>
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
