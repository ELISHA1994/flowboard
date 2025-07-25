'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  ChevronLeft,
  ChevronRight,
  Home,
  CheckSquare,
  Calendar,
  Users,
  BarChart3,
  Settings,
  Inbox,
  Plus,
  Search,
  Hash,
  Folder,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'My Tasks', href: '/tasks', icon: CheckSquare },
  { name: 'Categories', href: '/categories', icon: Folder },
  { name: 'Tags', href: '/tags', icon: Hash },
  { name: 'Inbox', href: '/inbox', icon: Inbox },
  { name: 'Calendar', href: '/calendar', icon: Calendar },
  { name: 'Projects', href: '/projects', icon: Users },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div
      className={cn(
        'relative flex h-full flex-col border-r border-border gradient-dark transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg gradient-primary shadow-md" />
            <span className="text-xl font-bold">TaskMaster</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn('text-muted-foreground hover:text-foreground', collapsed && 'mx-auto')}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              className="w-full rounded-md border border-input bg-background py-2 pl-10 pr-4 text-sm placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="px-4 pb-4">
        <Button
          variant="primary"
          className={cn('w-full justify-start', collapsed && 'justify-center px-0')}
          size={collapsed ? 'icon' : 'default'}
        >
          <Plus className="h-4 w-4" />
          {!collapsed && <span className="ml-2">New Task</span>}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center rounded-md px-2 py-2 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary/20 text-primary shadow-sm border border-primary/30'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                collapsed && 'justify-center'
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span className="ml-3">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Settings */}
      <div className="border-t border-border p-4">
        <Link
          href="/settings"
          className={cn(
            'flex items-center rounded-md px-2 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-accent hover:text-accent-foreground',
            collapsed && 'justify-center'
          )}
        >
          <Settings className="h-5 w-5 shrink-0" />
          {!collapsed && <span className="ml-3">Settings</span>}
        </Link>
      </div>
    </div>
  );
}
