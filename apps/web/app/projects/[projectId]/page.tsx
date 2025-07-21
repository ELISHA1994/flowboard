'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { EditProjectModal } from '@/components/projects/edit-project-modal';
import { AddMemberModal } from '@/components/projects/add-member-modal';
import { Project, ProjectMember, ProjectsService } from '@/lib/api/projects';
import { Task, TasksService } from '@/lib/api/tasks';
import { AuthService } from '@/lib/auth';
import { useToastContext } from '@/contexts/toast-context';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ArrowLeft,
  Edit,
  MoreVertical,
  Plus,
  Users,
  CheckSquare,
  Clock,
  AlertCircle,
  Crown,
  Shield,
  Eye,
  User,
  Trash2,
  Circle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToastContext();
  const projectId = params.projectId as string;

  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [addMemberModalOpen, setAddMemberModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ id: string } | null>(null);

  // Fetch current user
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const user = await AuthService.getCurrentUser();
        setCurrentUser(user);
      } catch (error) {
        console.error('Failed to fetch current user:', error);
      }
    };
    fetchUser();
  }, []);

  // Fetch project details
  const fetchProjectData = async () => {
    try {
      setLoading(true);

      // Fetch project
      const projectData = await ProjectsService.getProject(projectId);
      setProject(projectData);

      // Fetch members
      const membersData = await ProjectsService.getProjectMembers(projectId);
      setMembers(membersData);

      // Fetch tasks
      const tasksData = await TasksService.getTasks({ project_id: projectId });
      setTasks(tasksData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load project details.',
        variant: 'destructive',
      });
      router.push('/projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  if (loading || !project) {
    return (
      <DashboardLayout>
        <div className="flex-1 space-y-4 p-8 pt-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-64" />
        </div>
      </DashboardLayout>
    );
  }

  const userRole = currentUser
    ? ProjectsService.getUserRole(project, members, currentUser.id)
    : null;
  const canEdit = ProjectsService.canEditProject(userRole);
  const canManageMembers = ProjectsService.canManageMembers(userRole);

  // Task statistics (ensure tasks is always an array)
  const safeTasks = Array.isArray(tasks) ? tasks : [];
  const taskStats = {
    total: safeTasks.length,
    todo: safeTasks.filter((t) => t.status === 'todo').length,
    inProgress: safeTasks.filter((t) => t.status === 'in_progress').length,
    done: safeTasks.filter((t) => t.status === 'done').length,
    overdue: safeTasks.filter(
      (t) => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'done'
    ).length,
  };

  const getRoleIcon = (role: ProjectMember['role']) => {
    switch (role) {
      case 'owner':
        return <Crown className="h-4 w-4" />;
      case 'admin':
        return <Shield className="h-4 w-4" />;
      case 'member':
        return <User className="h-4 w-4" />;
      case 'viewer':
        return <Eye className="h-4 w-4" />;
    }
  };

  const getRoleBadgeVariant = (role: ProjectMember['role']) => {
    switch (role) {
      case 'owner':
        return 'default';
      case 'admin':
        return 'secondary';
      case 'member':
        return 'outline';
      case 'viewer':
        return 'outline';
    }
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/projects')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Projects
            </Button>

            <div className="flex items-center gap-3">
              <div
                className="h-6 w-6 rounded-full"
                style={{
                  backgroundColor: ProjectsService.formatProjectColor(project.color),
                }}
              />
              <div>
                <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
                {project.description && (
                  <p className="text-muted-foreground">{project.description}</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={() => router.push(`/tasks?project_id=${projectId}`)} className="gap-2">
              <CheckSquare className="h-4 w-4" />
              View Tasks
            </Button>
            {canEdit && (
              <Button variant="outline" onClick={() => setEditModalOpen(true)} className="gap-2">
                <Edit className="h-4 w-4" />
                Edit
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="members">Members ({members.length})</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            {/* Task Statistics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
                  <CheckSquare className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{taskStats.total}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">To Do</CardTitle>
                  <Circle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{taskStats.todo}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">In Progress</CardTitle>
                  <Clock className="h-4 w-4 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{taskStats.inProgress}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Completed</CardTitle>
                  <CheckSquare className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{taskStats.done}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Overdue</CardTitle>
                  <AlertCircle className="h-4 w-4 text-red-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">{taskStats.overdue}</div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest updates in this project</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">Activity tracking coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Members Tab */}
          <TabsContent value="members" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Project Members</CardTitle>
                    <CardDescription>Manage who has access to this project</CardDescription>
                  </div>
                  {canManageMembers && (
                    <Button size="sm" className="gap-2" onClick={() => setAddMemberModalOpen(true)}>
                      <Plus className="h-4 w-4" />
                      Add Member
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {members.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                          <span className="text-sm font-semibold">
                            {member.user?.username?.[0]?.toUpperCase() || 'U'}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium">
                            {member.user?.username || 'Unknown User'}
                            {member.user_id === currentUser?.id && (
                              <span className="ml-2 text-sm text-muted-foreground">(You)</span>
                            )}
                          </p>
                          <p className="text-sm text-muted-foreground">{member.user?.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant={getRoleBadgeVariant(member.role)} className="gap-1">
                          {getRoleIcon(member.role)}
                          {member.role}
                        </Badge>

                        {canManageMembers && member.role !== 'owner' && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <Shield className="mr-2 h-4 w-4" />
                                Change Role
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive">
                                <Trash2 className="mr-2 h-4 w-4" />
                                Remove from Project
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Project Settings</CardTitle>
                <CardDescription>Manage project preferences and configurations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium">Created</h4>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium">Last Updated</h4>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium">Your Role</h4>
                    <Badge
                      variant={getRoleBadgeVariant(userRole || 'viewer')}
                      className="gap-1 mt-1"
                    >
                      {getRoleIcon(userRole || 'viewer')}
                      {userRole || 'No Role'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Edit Project Modal */}
        <EditProjectModal
          project={project}
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          onProjectUpdated={fetchProjectData}
        />

        {/* Add Member Modal */}
        {project && (
          <AddMemberModal
            open={addMemberModalOpen}
            onOpenChange={setAddMemberModalOpen}
            projectId={project.id}
            currentMembers={members}
            onMemberAdded={(newMember) => {
              setMembers([...members, newMember]);
              setAddMemberModalOpen(false);
            }}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
