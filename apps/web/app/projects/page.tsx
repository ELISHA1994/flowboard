'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { CreateProjectModal } from '@/components/projects/create-project-modal';
import { EditProjectModal } from '@/components/projects/edit-project-modal';
import { ProjectCard } from '@/components/projects/project-card';
import { Project, ProjectMember, ProjectsService } from '@/lib/api/projects';
import { AuthService } from '@/lib/auth';
import { useToastContext } from '@/contexts/toast-context';
import { Skeleton } from '@/components/ui/skeleton';
import { FolderPlus, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function ProjectsPage() {
  const { toast } = useToastContext();
  const [projects, setProjects] = useState<Project[]>([]);
  const [membersByProject, setMembersByProject] = useState<Record<string, ProjectMember[]>>({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingProject, setEditingProject] = useState<Project | null>(null);
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

  // Fetch projects
  const fetchProjects = async () => {
    try {
      setLoading(true);
      const projectList = await ProjectsService.getProjects();
      setProjects(projectList);

      // Fetch members for each project
      const membersData: Record<string, ProjectMember[]> = {};
      await Promise.all(
        projectList.map(async (project) => {
          try {
            const members = await ProjectsService.getProjectMembers(project.id);
            membersData[project.id] = members;
          } catch (error) {
            console.error(`Failed to fetch members for project ${project.id}:`, error);
            membersData[project.id] = [];
          }
        })
      );
      setMembersByProject(membersData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load projects. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Filter projects based on search
  const filteredProjects = projects.filter(
    (project) =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
            <p className="text-muted-foreground">
              Organize your tasks and collaborate with your team
            </p>
          </div>
          <CreateProjectModal onProjectCreated={fetchProjects} />
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-[200px]" />
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
            <FolderPlus className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold">No projects found</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {searchQuery
                ? 'Try adjusting your search query'
                : 'Create your first project to get started'}
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                members={membersByProject[project.id] || []}
                currentUserId={currentUser?.id}
                onEdit={() => setEditingProject(project)}
                onDelete={fetchProjects}
                onManageMembers={() => {
                  // TODO: Implement member management modal
                  toast({
                    title: 'Coming soon',
                    description: 'Member management will be available soon.',
                  });
                }}
              />
            ))}
          </div>
        )}

        {/* Edit Project Modal */}
        {editingProject && (
          <EditProjectModal
            project={editingProject}
            open={!!editingProject}
            onOpenChange={(open) => !open && setEditingProject(null)}
            onProjectUpdated={fetchProjects}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
