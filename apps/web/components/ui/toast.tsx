'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

export interface ToastProps {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
  onDismiss?: (id: string) => void;
}

export function Toast({ id, title, description, variant = 'default', onDismiss }: ToastProps) {
  return (
    <div
      className={cn(
        'pointer-events-auto flex w-full max-w-md rounded-lg border p-4 shadow-lg transition-all',
        variant === 'default'
          ? 'border-border bg-background text-foreground'
          : 'border-destructive bg-destructive text-destructive-foreground'
      )}
    >
      <div className="flex-1">
        {title && <div className="mb-1 font-semibold">{title}</div>}
        {description && <div className="text-sm opacity-90">{description}</div>}
      </div>
      {onDismiss && (
        <button
          onClick={() => onDismiss(id)}
          className="ml-4 inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-secondary focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>
      )}
    </div>
  );
}

export function ToastContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex flex-col items-end justify-end p-4 md:p-6">
      <div className="flex w-full flex-col items-center space-y-2">{children}</div>
    </div>
  );
}
