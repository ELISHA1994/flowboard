'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Hash,
  CheckSquare,
  Tags,
  Filter,
} from 'lucide-react';
import { useTagsQuery, usePopularTagsQuery, useDeleteTagMutation } from '@/hooks/use-tags-query';
import { Tag, TagsService } from '@/lib/api/tags';
import { cn } from '@/lib/utils';
import { CreateTagModal } from '@/components/tags/create-tag-modal';
import { EditTagModal } from '@/components/tags/edit-tag-modal';
import { BulkCreateTagsModal } from '@/components/tags/bulk-create-tags-modal';

export default function TagsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [bulkCreateModalOpen, setBulkCreateModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deletingTag, setDeletingTag] = useState<Tag | null>(null);
  const [showPopular, setShowPopular] = useState(false);

  // Fetch tags
  const { data: allTags = [], isLoading: allTagsLoading } = useTagsQuery();
  const { data: popularTags = [], isLoading: popularTagsLoading } = usePopularTagsQuery(20);
  const deleteTag = useDeleteTagMutation();

  const tags = showPopular ? popularTags : allTags;
  const isLoading = showPopular ? popularTagsLoading : allTagsLoading;

  // Filter tags based on search
  const filteredTags = tags.filter((tag) =>
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDelete = async () => {
    if (deletingTag) {
      await deleteTag.mutateAsync(deletingTag.id);
      setDeletingTag(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Tags</h2>
            <p className="text-muted-foreground">Label and organize your tasks with tags</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setBulkCreateModalOpen(true)}>
              <Tags className="mr-2 h-4 w-4" />
              Bulk Create
            </Button>
            <Button variant="primary" onClick={() => setCreateModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Tag
            </Button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant={showPopular ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowPopular(!showPopular)}
          >
            <Filter className="mr-2 h-4 w-4" />
            {showPopular ? 'Popular' : 'All Tags'}
          </Button>
        </div>

        {/* Tags Display */}
        {isLoading ? (
          <div className="flex flex-wrap gap-2">
            {[...Array(20)].map((_, i) => (
              <Skeleton key={i} className="h-8 w-24" />
            ))}
          </div>
        ) : filteredTags.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Hash className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-semibold">No tags found</h3>
              <p className="text-sm text-muted-foreground mt-2">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Create your first tag to get started'}
              </p>
              {!searchQuery && (
                <Button onClick={() => setCreateModalOpen(true)} className="mt-4" variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Tag
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-medium">
                {showPopular ? 'Popular Tags' : 'All Tags'}
              </CardTitle>
              <CardDescription>
                {showPopular
                  ? 'Most frequently used tags'
                  : `${filteredTags.length} tag${filteredTags.length !== 1 ? 's' : ''} available`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {filteredTags.map((tag) => (
                  <div key={tag.id} className="group relative inline-flex items-center">
                    <Badge
                      variant="secondary"
                      className="pr-8 pl-3 py-1.5 text-sm"
                      style={{
                        backgroundColor: TagsService.formatTagColor(tag.color) + '20',
                        color: TagsService.formatTagColor(tag.color),
                        borderColor: TagsService.formatTagColor(tag.color),
                      }}
                    >
                      <Hash className="mr-1 h-3 w-3" />
                      {tag.name}
                      {tag.task_count !== undefined && tag.task_count > 0 && (
                        <span className="ml-2 text-xs opacity-75">{tag.task_count}</span>
                      )}
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={cn(
                            'absolute right-0 h-full px-2 rounded-l-none opacity-0 group-hover:opacity-100 transition-opacity',
                            'hover:bg-transparent'
                          )}
                          style={{
                            color: TagsService.formatTagColor(tag.color),
                          }}
                        >
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => setEditingTag(tag)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeletingTag(tag)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Create Tag Modal */}
        <CreateTagModal open={createModalOpen} onOpenChange={setCreateModalOpen} />

        {/* Bulk Create Tags Modal */}
        <BulkCreateTagsModal open={bulkCreateModalOpen} onOpenChange={setBulkCreateModalOpen} />

        {/* Edit Tag Modal */}
        {editingTag && (
          <EditTagModal
            tag={editingTag}
            open={!!editingTag}
            onOpenChange={(open) => !open && setEditingTag(null)}
          />
        )}

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={!!deletingTag} onOpenChange={(open) => !open && setDeletingTag(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Tag</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "#{deletingTag?.name}"? This will remove the tag
                from all associated tasks.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={deleteTag.isPending}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleteTag.isPending ? 'Deleting...' : 'Delete'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </DashboardLayout>
  );
}
