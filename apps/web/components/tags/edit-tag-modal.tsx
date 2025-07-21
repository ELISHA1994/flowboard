'use client';

import { useState, useEffect } from 'react';
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
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2, Hash } from 'lucide-react';
import { useUpdateTagMutation } from '@/hooks/use-tags-query';
import { Tag, UpdateTagRequest, TagsService } from '@/lib/api/tags';

interface EditTagModalProps {
  tag: Tag;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Predefined colors for tags
const TAG_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#f59e0b', // amber
  '#eab308', // yellow
  '#84cc16', // lime
  '#22c55e', // green
  '#10b981', // emerald
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#0ea5e9', // sky
  '#3b82f6', // blue
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#a855f7', // purple
  '#d946ef', // fuchsia
  '#ec4899', // pink
  '#f43f5e', // rose
  '#6b7280', // gray
];

export function EditTagModal({ tag, open, onOpenChange }: EditTagModalProps) {
  const updateTag = useUpdateTagMutation();
  const [formData, setFormData] = useState<UpdateTagRequest>({
    name: tag.name,
    color: TagsService.formatTagColor(tag.color),
  });
  const [error, setError] = useState('');

  // Reset form when tag changes
  useEffect(() => {
    setFormData({
      name: tag.name,
      color: TagsService.formatTagColor(tag.color),
    });
    setError('');
  }, [tag]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.name?.trim()) {
      setError('Tag name is required');
      return;
    }

    // Format tag name
    const formattedName = TagsService.formatTagName(formData.name);

    // Validate tag name
    if (!TagsService.validateTagName(formattedName)) {
      setError('Tag name can only contain lowercase letters, numbers, hyphens, and underscores');
      return;
    }

    await updateTag.mutateAsync({
      id: tag.id,
      data: {
        name: formattedName,
        color: formData.color,
      },
    });

    // Close modal on success
    if (!updateTag.error) {
      onOpenChange(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: tag.name,
      color: TagsService.formatTagColor(tag.color),
    });
    setError('');
    updateTag.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Tag</DialogTitle>
            <DialogDescription>Update the tag details.</DialogDescription>
          </DialogHeader>

          {(updateTag.error || error) && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error || updateTag.error?.message || 'Failed to update tag'}
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Tag Name *</Label>
              <Input
                id="name"
                placeholder="e.g., urgent, feature, bug-fix"
                value={formData.name || ''}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  setError('');
                }}
                disabled={updateTag.isPending}
                required
              />
              <p className="text-xs text-muted-foreground">Spaces will be replaced with hyphens</p>
            </div>

            <div className="grid gap-2">
              <Label>Color</Label>
              <div className="grid grid-cols-9 gap-2">
                {TAG_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className={`h-8 w-8 rounded-md border-2 transition-all ${
                      formData.color === color
                        ? 'border-gray-900 dark:border-gray-100 scale-110'
                        : 'border-transparent hover:scale-105'
                    }`}
                    style={{ backgroundColor: color }}
                    onClick={() => setFormData({ ...formData, color })}
                    disabled={updateTag.isPending}
                  />
                ))}
              </div>
            </div>

            {/* Preview */}
            <div className="grid gap-2">
              <Label>Preview</Label>
              <div className="flex items-center gap-2">
                <div
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium"
                  style={{
                    backgroundColor: (formData.color || TAG_COLORS[10]) + '20',
                    color: formData.color || TAG_COLORS[10],
                  }}
                >
                  <Hash className="h-3 w-3" />
                  {formData.name ? TagsService.formatTagName(formData.name) : 'tag-name'}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={updateTag.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateTag.isPending}>
              {updateTag.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {updateTag.isPending ? 'Updating...' : 'Update Tag'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
