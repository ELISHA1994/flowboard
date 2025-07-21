'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, Palette } from 'lucide-react';
import { Project, ProjectsService, UpdateProjectRequest } from '@/lib/api/projects';
import { useToastContext } from '@/contexts/toast-context';
import { cn } from '@/lib/utils';

interface EditProjectModalProps {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectUpdated?: () => void;
}

const PROJECT_COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#ef4444', // red
  '#f97316', // orange
  '#f59e0b', // amber
  '#84cc16', // lime
  '#10b981', // emerald
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#6b7280', // gray
];

export function EditProjectModal({
  project,
  open,
  onOpenChange,
  onProjectUpdated,
}: EditProjectModalProps) {
  const { toast } = useToastContext();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<UpdateProjectRequest>({
    name: project.name,
    description: project.description || '',
    color: project.color || PROJECT_COLORS[0],
  });
  const [errors, setErrors] = useState<Partial<UpdateProjectRequest>>({});

  // Update form when project changes
  useEffect(() => {
    setFormData({
      name: project.name,
      description: project.description || '',
      color: project.color || PROJECT_COLORS[0],
    });
  }, [project]);

  const validateForm = (): boolean => {
    const newErrors: Partial<UpdateProjectRequest> = {};

    if (formData.name && !formData.name.trim()) {
      newErrors.name = 'Project name is required';
    } else if (formData.name && formData.name.length > 100) {
      newErrors.name = 'Project name must be less than 100 characters';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      // Only send changed fields
      const updates: UpdateProjectRequest = {};
      if (formData.name !== project.name) updates.name = formData.name;
      if (formData.description !== project.description) updates.description = formData.description;
      if (formData.color !== project.color) updates.color = formData.color;

      if (Object.keys(updates).length === 0) {
        toast({
          title: 'No changes',
          description: 'No changes were made to the project.',
        });
        onOpenChange(false);
        return;
      }

      await ProjectsService.updateProject(project.id, updates);

      toast({
        title: 'Project updated',
        description: 'Project has been updated successfully.',
      });

      onOpenChange(false);

      if (onProjectUpdated) {
        onProjectUpdated();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update project',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
            <DialogDescription>Make changes to your project details.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Project Name */}
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Project Name</Label>
              <Input
                id="edit-name"
                placeholder="e.g., Website Redesign"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  if (errors.name) {
                    setErrors({ ...errors, name: undefined });
                  }
                }}
                className={cn(errors.name && 'border-destructive')}
              />
              {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                placeholder="Brief description of the project..."
                value={formData.description}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value });
                  if (errors.description) {
                    setErrors({ ...errors, description: undefined });
                  }
                }}
                rows={3}
                className={cn(errors.description && 'border-destructive')}
              />
              {errors.description && (
                <p className="text-sm text-destructive">{errors.description}</p>
              )}
            </div>

            {/* Color Selection */}
            <div className="grid gap-2">
              <Label>Project Color</Label>
              <div className="flex items-center gap-2">
                <Palette className="h-4 w-4 text-muted-foreground" />
                <div className="flex flex-wrap gap-2">
                  {PROJECT_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      className={cn(
                        'h-8 w-8 rounded-md border-2 transition-all',
                        formData.color === color
                          ? 'border-foreground scale-110'
                          : 'border-transparent hover:scale-105'
                      )}
                      style={{ backgroundColor: color }}
                      onClick={() => setFormData({ ...formData, color })}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
