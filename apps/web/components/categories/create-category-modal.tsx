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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useCreateCategoryMutation } from '@/hooks/use-categories-query';
import { CreateCategoryRequest } from '@/lib/api/categories';

interface CreateCategoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Predefined colors for categories
const CATEGORY_COLORS = [
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

// Predefined icons for categories
const CATEGORY_ICONS = [
  '📁',
  '📂',
  '🏷️',
  '🎯',
  '💼',
  '📊',
  '💡',
  '🚀',
  '⭐',
  '🔥',
  '💎',
  '🎨',
  '🛠️',
  '📚',
  '🏠',
  '🌟',
  '⚡',
  '🌈',
  '🎪',
  '🎭',
  '🎮',
  '🎬',
  '🎵',
  '🍕',
];

export function CreateCategoryModal({ open, onOpenChange }: CreateCategoryModalProps) {
  const createCategory = useCreateCategoryMutation();
  const [formData, setFormData] = useState<CreateCategoryRequest>({
    name: '',
    description: '',
    color: CATEGORY_COLORS[0],
    icon: CATEGORY_ICONS[0],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      return;
    }

    await createCategory.mutateAsync(formData);

    // Reset form and close modal on success
    if (!createCategory.error) {
      setFormData({
        name: '',
        description: '',
        color: CATEGORY_COLORS[0],
        icon: CATEGORY_ICONS[0],
      });
      onOpenChange(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: '',
      description: '',
      color: CATEGORY_COLORS[0],
      icon: CATEGORY_ICONS[0],
    });
    createCategory.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Category</DialogTitle>
            <DialogDescription>Add a new category to organize your tasks.</DialogDescription>
          </DialogHeader>

          {createCategory.error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {createCategory.error.message || 'Failed to create category'}
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="Enter category name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={createCategory.isPending}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter category description (optional)"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={createCategory.isPending}
                rows={3}
              />
            </div>

            <div className="grid gap-2">
              <Label>Color</Label>
              <div className="grid grid-cols-9 gap-2">
                {CATEGORY_COLORS.map((color) => (
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
                    disabled={createCategory.isPending}
                  />
                ))}
              </div>
            </div>

            <div className="grid gap-2">
              <Label>Icon</Label>
              <div className="grid grid-cols-8 gap-2">
                {CATEGORY_ICONS.map((icon) => (
                  <button
                    key={icon}
                    type="button"
                    className={`h-10 w-10 rounded-md border-2 text-lg transition-all flex items-center justify-center ${
                      formData.icon === icon
                        ? 'border-gray-900 dark:border-gray-100 scale-110'
                        : 'border-gray-200 dark:border-gray-700 hover:scale-105'
                    }`}
                    onClick={() => setFormData({ ...formData, icon })}
                    disabled={createCategory.isPending}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            {/* Preview */}
            <div className="grid gap-2">
              <Label>Preview</Label>
              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <div
                  className="h-10 w-10 rounded-lg flex items-center justify-center text-lg"
                  style={{
                    backgroundColor: formData.color + '20',
                    color: formData.color,
                  }}
                >
                  {formData.icon}
                </div>
                <div>
                  <p className="font-medium">{formData.name || 'Category Name'}</p>
                  {formData.description && (
                    <p className="text-sm text-muted-foreground">{formData.description}</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createCategory.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createCategory.isPending}>
              {createCategory.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {createCategory.isPending ? 'Creating...' : 'Create Category'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
