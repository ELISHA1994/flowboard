'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MoreVertical, Edit, Trash2, Users, FolderOpen, Clock, CheckSquare } from 'lucide-react';
import { Project, ProjectMember, ProjectsService } from '@/lib/api/projects';
import { useToastContext } from '@/contexts/toast-context';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface ProjectCardProps {
  project: Project;
  members?: ProjectMember[];
  currentUserId?: string;
  taskCount?: number;
  onEdit?: () => void;
  onDelete?: () => void;
  onManageMembers?: () => void;
}

export function ProjectCard({
  project,
  members = [],
  currentUserId,
  taskCount = 0,
  onEdit,
  onDelete,
  onManageMembers,
}: ProjectCardProps) {
  const router = useRouter();
  const { toast } = useToastContext();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const userRole = currentUserId
    ? ProjectsService.getUserRole(project, members, currentUserId)
    : null;
  const canEdit = ProjectsService.canEditProject(userRole);
  const canManageMembers = ProjectsService.canManageMembers(userRole);

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await ProjectsService.deleteProject(project.id);

      toast({
        title: 'Project deleted',
        description: `"${project.name}" has been deleted successfully.`,
      });

      setShowDeleteDialog(false);
      if (onDelete) {
        onDelete();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete project. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const handleCardClick = () => {
    router.push(`/projects/${project.id}`);
  };

  return (
    <>
      <Card className="cursor-pointer transition-all hover:shadow-md" onClick={handleCardClick}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              {/* Project color indicator */}
              <div
                className="mt-1 h-4 w-4 rounded-full flex-shrink-0"
                style={{
                  backgroundColor: ProjectsService.formatProjectColor(project.color),
                }}
              />
              <div className="space-y-1">
                <CardTitle className="text-lg">{project.name}</CardTitle>
                {project.description && (
                  <CardDescription className="line-clamp-2">{project.description}</CardDescription>
                )}
              </div>
            </div>

            {/* Actions dropdown */}
            {(canEdit || canManageMembers) && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCardClick();
                    }}
                  >
                    <FolderOpen className="mr-2 h-4 w-4" />
                    View Project
                  </DropdownMenuItem>
                  {canEdit && (
                    <>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onEdit) onEdit();
                        }}
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        Edit Project
                      </DropdownMenuItem>
                    </>
                  )}
                  {canManageMembers && (
                    <DropdownMenuItem
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onManageMembers) onManageMembers();
                      }}
                    >
                      <Users className="mr-2 h-4 w-4" />
                      Manage Members
                    </DropdownMenuItem>
                  )}
                  {canEdit && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteDialog(true);
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete Project
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {/* Project stats */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <CheckSquare className="h-4 w-4" />
              <span>{taskCount} tasks</span>
            </div>
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{members.length} members</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              <span>
                Updated {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
              </span>
            </div>
          </div>

          {/* User role badge */}
          {userRole && (
            <div className="mt-3">
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  userRole === 'owner' && 'border-purple-500 text-purple-600',
                  userRole === 'admin' && 'border-blue-500 text-blue-600',
                  userRole === 'member' && 'border-green-500 text-green-600',
                  userRole === 'viewer' && 'border-gray-500 text-gray-600'
                )}
              >
                {userRole}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{project.name}"? This action cannot be undone. All
              tasks and data associated with this project will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? 'Deleting...' : 'Delete Project'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
