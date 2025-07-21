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
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useUpdateCategoryMutation } from '@/hooks/use-categories-query';
import { Category, UpdateCategoryRequest, CategoriesService } from '@/lib/api/categories';

interface EditCategoryModalProps {
  category: Category;
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

export function EditCategoryModal({ category, open, onOpenChange }: EditCategoryModalProps) {
  const updateCategory = useUpdateCategoryMutation();
  const [formData, setFormData] = useState<UpdateCategoryRequest>({
    name: category.name,
    description: category.description || '',
    color: CategoriesService.formatCategoryColor(category.color),
    icon: CategoriesService.formatCategoryIcon(category.icon),
    is_active: category.is_active,
  });

  // Reset form when category changes
  useEffect(() => {
    setFormData({
      name: category.name,
      description: category.description || '',
      color: CategoriesService.formatCategoryColor(category.color),
      icon: CategoriesService.formatCategoryIcon(category.icon),
      is_active: category.is_active,
    });
  }, [category]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name?.trim()) {
      return;
    }

    await updateCategory.mutateAsync({
      id: category.id,
      data: formData,
    });

    // Close modal on success
    if (!updateCategory.error) {
      onOpenChange(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: category.name,
      description: category.description || '',
      color: CategoriesService.formatCategoryColor(category.color),
      icon: CategoriesService.formatCategoryIcon(category.icon),
      is_active: category.is_active,
    });
    updateCategory.reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Category</DialogTitle>
            <DialogDescription>Update the category details.</DialogDescription>
          </DialogHeader>

          {updateCategory.error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {updateCategory.error.message || 'Failed to update category'}
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="Enter category name"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={updateCategory.isPending}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter category description (optional)"
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={updateCategory.isPending}
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
                    disabled={updateCategory.isPending}
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
                    disabled={updateCategory.isPending}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label htmlFor="is_active">Active</Label>
                <p className="text-sm text-muted-foreground">
                  Inactive categories won't be shown in task forms
                </p>
              </div>
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                disabled={updateCategory.isPending}
              />
            </div>

            {/* Preview */}
            <div className="grid gap-2">
              <Label>Preview</Label>
              <div className="flex items-center gap-3 p-3 rounded-lg border">
                <div
                  className="h-10 w-10 rounded-lg flex items-center justify-center text-lg"
                  style={{
                    backgroundColor: (formData.color || CATEGORY_COLORS[0]) + '20',
                    color: formData.color || CATEGORY_COLORS[0],
                  }}
                >
                  {formData.icon || CATEGORY_ICONS[0]}
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
              disabled={updateCategory.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateCategory.isPending}>
              {updateCategory.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {updateCategory.isPending ? 'Updating...' : 'Update Category'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
