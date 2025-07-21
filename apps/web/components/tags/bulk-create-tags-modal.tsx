'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2, Hash, Info } from 'lucide-react';
import { useCreateBulkTagsMutation } from '@/hooks/use-tags-query';
import { BulkTagCreate, TagsService } from '@/lib/api/tags';

interface BulkCreateTagsModalProps {
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

export function BulkCreateTagsModal({ open, onOpenChange }: BulkCreateTagsModalProps) {
  const createBulkTags = useCreateBulkTagsMutation();
  const [formData, setFormData] = useState<{
    names: string;
    color: string;
  }>({
    names: '',
    color: TAG_COLORS[10], // Default blue
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.names.trim()) {
      setError('Please enter at least one tag name');
      return;
    }

    // Parse tag names from textarea
    const tagNames = formData.names
      .split(/[\n,]+/) // Split by newlines or commas
      .map((name) => name.trim())
      .filter((name) => name.length > 0)
      .map((name) => TagsService.formatTagName(name));

    // Remove duplicates
    const uniqueTagNames = [...new Set(tagNames)];

    // Validate all tag names
    const invalidTags = uniqueTagNames.filter((name) => !TagsService.validateTagName(name));
    if (invalidTags.length > 0) {
      setError(`Invalid tag names: ${invalidTags.join(', ')}`);
      return;
    }

    if (uniqueTagNames.length === 0) {
      setError('No valid tag names provided');
      return;
    }

    const bulkData: BulkTagCreate = {
      names: uniqueTagNames,
      color: formData.color,
    };

    await createBulkTags.mutateAsync(bulkData);

    // Reset form and close modal on success
    if (!createBulkTags.error) {
      setFormData({
        names: '',
        color: TAG_COLORS[10],
      });
      onOpenChange(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      names: '',
      color: TAG_COLORS[10],
    });
    setError('');
    createBulkTags.reset();
    onOpenChange(false);
  };

  // Preview tags
  const previewTags = formData.names
    .split(/[\n,]+/)
    .map((name) => name.trim())
    .filter((name) => name.length > 0)
    .map((name) => TagsService.formatTagName(name))
    .filter((name, index, arr) => arr.indexOf(name) === index) // Remove duplicates
    .slice(0, 10); // Show max 10 preview tags

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Bulk Create Tags</DialogTitle>
            <DialogDescription>
              Create multiple tags at once. All tags will have the same color.
            </DialogDescription>
          </DialogHeader>

          <Alert className="mt-4">
            <Info className="h-4 w-4" />
            <AlertDescription>
              Enter one tag per line or separate with commas. Spaces will be replaced with hyphens.
            </AlertDescription>
          </Alert>

          {(createBulkTags.error || error) && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error || createBulkTags.error?.message || 'Failed to create tags'}
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="names">Tag Names *</Label>
              <Textarea
                id="names"
                placeholder="urgent&#10;feature&#10;bug-fix&#10;documentation&#10;testing"
                value={formData.names}
                onChange={(e) => {
                  setFormData({ ...formData, names: e.target.value });
                  setError('');
                }}
                disabled={createBulkTags.isPending}
                rows={6}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label>Color (for all tags)</Label>
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
                    disabled={createBulkTags.isPending}
                  />
                ))}
              </div>
            </div>

            {/* Preview */}
            {previewTags.length > 0 && (
              <div className="grid gap-2">
                <Label>Preview</Label>
                <div className="flex flex-wrap gap-2 p-3 rounded-lg border">
                  {previewTags.map((tag, index) => (
                    <div
                      key={index}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium"
                      style={{
                        backgroundColor: formData.color + '20',
                        color: formData.color,
                      }}
                    >
                      <Hash className="h-3 w-3" />
                      {tag}
                    </div>
                  ))}
                  {formData.names.split(/[\n,]+/).filter((name) => name.trim()).length > 10 && (
                    <span className="text-sm text-muted-foreground">
                      +{formData.names.split(/[\n,]+/).filter((name) => name.trim()).length - 10}{' '}
                      more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createBulkTags.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createBulkTags.isPending || previewTags.length === 0}>
              {createBulkTags.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {createBulkTags.isPending
                ? 'Creating...'
                : `Create ${previewTags.length} Tag${previewTags.length !== 1 ? 's' : ''}`}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
