'use client';

import React, { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Bookmark, Star, Search, MoreVertical, Pencil, Trash2, Plus, StarOff } from 'lucide-react';
import { AdvancedFilters } from './advanced-filters-modal';

export interface SavedSearch {
  id: string;
  name: string;
  description?: string;
  filters: AdvancedFilters;
  isPinned: boolean;
  createdAt: Date;
  updatedAt: Date;
}

interface SavedSearchesProps {
  onApplySearch: (filters: AdvancedFilters) => void;
  currentFilters: AdvancedFilters;
}

export function SavedSearches({ onApplySearch, currentFilters }: SavedSearchesProps) {
  const { toast } = useToast();
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(() => {
    // Load from localStorage
    const stored = localStorage.getItem('taskmaster-saved-searches');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        return parsed.map((s: any) => ({
          ...s,
          createdAt: new Date(s.createdAt),
          updatedAt: new Date(s.updatedAt),
        }));
      } catch {
        return [];
      }
    }
    return [];
  });
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [editingSearch, setEditingSearch] = useState<SavedSearch | null>(null);
  const [searchName, setSearchName] = useState('');
  const [searchDescription, setSearchDescription] = useState('');

  // Sort searches by pinned first, then by updated date
  const sortedSearches = [...savedSearches].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return b.updatedAt.getTime() - a.updatedAt.getTime();
  });

  const saveToLocalStorage = (searches: SavedSearch[]) => {
    localStorage.setItem('taskmaster-saved-searches', JSON.stringify(searches));
  };

  const handleSaveSearch = () => {
    if (!searchName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a name for the search',
        variant: 'destructive',
      });
      return;
    }

    const newSearch: SavedSearch = {
      id: editingSearch?.id || Date.now().toString(),
      name: searchName,
      description: searchDescription,
      filters: currentFilters,
      isPinned: editingSearch?.isPinned || false,
      createdAt: editingSearch?.createdAt || new Date(),
      updatedAt: new Date(),
    };

    let updatedSearches;
    if (editingSearch) {
      updatedSearches = savedSearches.map((s) => (s.id === editingSearch.id ? newSearch : s));
    } else {
      updatedSearches = [...savedSearches, newSearch];
    }

    setSavedSearches(updatedSearches);
    saveToLocalStorage(updatedSearches);
    setSaveDialogOpen(false);
    setEditingSearch(null);
    setSearchName('');
    setSearchDescription('');

    toast({
      title: editingSearch ? 'Search updated' : 'Search saved',
      description: `"${searchName}" has been ${editingSearch ? 'updated' : 'saved'}`,
    });
  };

  const handleDeleteSearch = (search: SavedSearch) => {
    const updatedSearches = savedSearches.filter((s) => s.id !== search.id);
    setSavedSearches(updatedSearches);
    saveToLocalStorage(updatedSearches);

    toast({
      title: 'Search deleted',
      description: `"${search.name}" has been deleted`,
    });
  };

  const handleTogglePin = (search: SavedSearch) => {
    const updatedSearches = savedSearches.map((s) =>
      s.id === search.id ? { ...s, isPinned: !s.isPinned } : s
    );
    setSavedSearches(updatedSearches);
    saveToLocalStorage(updatedSearches);

    toast({
      title: search.isPinned ? 'Unpinned' : 'Pinned',
      description: `"${search.name}" has been ${search.isPinned ? 'unpinned' : 'pinned'}`,
    });
  };

  const handleEditSearch = (search: SavedSearch) => {
    setEditingSearch(search);
    setSearchName(search.name);
    setSearchDescription(search.description || '');
    setSaveDialogOpen(true);
  };

  const getFilterCount = (filters: AdvancedFilters) => {
    let count = 0;
    if (filters.searchQuery) count++;
    if (filters.status && filters.status !== 'all') count++;
    if (filters.priority && filters.priority !== 'all') count++;
    if (filters.projectId && filters.projectId !== 'all') count++;
    if (filters.categoryIds && filters.categoryIds.length > 0) count++;
    if (filters.tagIds && filters.tagIds.length > 0) count++;
    if (filters.assignedToId && filters.assignedToId !== 'all') count++;
    if (filters.dueDateFrom || filters.dueDateTo) count++;
    if (filters.createdDateFrom || filters.createdDateTo) count++;
    return count;
  };

  const hasActiveFilters = getFilterCount(currentFilters) > 0;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm">
            <Bookmark className="mr-2 h-4 w-4" />
            Saved Searches
            {sortedSearches.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {sortedSearches.length}
              </Badge>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-[300px]">
          <DropdownMenuLabel>Saved Searches</DropdownMenuLabel>
          {hasActiveFilters && (
            <>
              <DropdownMenuItem onClick={() => setSaveDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Save current search
              </DropdownMenuItem>
              <DropdownMenuSeparator />
            </>
          )}
          {sortedSearches.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No saved searches yet
            </div>
          ) : (
            sortedSearches.map((search) => (
              <div key={search.id} className="group relative">
                <DropdownMenuItem onClick={() => onApplySearch(search.filters)} className="pr-8">
                  <div className="flex items-start gap-2 flex-1">
                    {search.isPinned && <Star className="h-3 w-3 mt-0.5 text-yellow-500" />}
                    <div className="flex-1">
                      <div className="font-medium">{search.name}</div>
                      {search.description && (
                        <div className="text-xs text-muted-foreground">{search.description}</div>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {getFilterCount(search.filters)} filters
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(search.updatedAt).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </DropdownMenuItem>
                <div className="absolute right-2 top-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEditSearch(search)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleTogglePin(search)}>
                        {search.isPinned ? (
                          <>
                            <StarOff className="mr-2 h-4 w-4" />
                            Unpin
                          </>
                        ) : (
                          <>
                            <Star className="mr-2 h-4 w-4" />
                            Pin
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleDeleteSearch(search)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingSearch ? 'Edit Saved Search' : 'Save Current Search'}</DialogTitle>
            <DialogDescription>
              Give your search a name and optional description to easily find it later
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="search-name">Name</Label>
              <Input
                id="search-name"
                placeholder="e.g., High Priority Bugs"
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="search-description">Description (optional)</Label>
              <Input
                id="search-description"
                placeholder="e.g., All high priority tasks with bug tag"
                value={searchDescription}
                onChange={(e) => setSearchDescription(e.target.value)}
              />
            </div>
            <div className="text-sm text-muted-foreground">
              This search includes {getFilterCount(currentFilters)} active filter
              {getFilterCount(currentFilters) !== 1 ? 's' : ''}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveSearch}>{editingSearch ? 'Update' : 'Save'} Search</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
