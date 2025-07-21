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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  AlertCircle,
  Loader2,
  Copy,
  Check,
  Users,
  Link as LinkIcon,
  Mail,
  UserPlus,
  Shield,
  Eye,
  Edit2,
  X,
} from 'lucide-react';
import { Task } from '@/lib/api/tasks';
import { useToast } from '@/hooks/use-toast';

interface ShareTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
}

type SharePermission = 'view' | 'edit';

interface ShareUser {
  id: string;
  email: string;
  name?: string;
  permission: SharePermission;
}

export function ShareTaskModal({ open, onOpenChange, task }: ShareTaskModalProps) {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'people' | 'link'>('people');
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState<SharePermission>('view');
  const [message, setMessage] = useState('');
  const [linkCopied, setLinkCopied] = useState(false);
  const [linkEnabled, setLinkEnabled] = useState(false);
  const [linkPermission, setLinkPermission] = useState<SharePermission>('view');

  // Mock shared users - in a real app, this would come from the API
  const [sharedUsers, setSharedUsers] = useState<ShareUser[]>([
    {
      id: '1',
      email: 'john.doe@example.com',
      name: 'John Doe',
      permission: 'edit',
    },
    {
      id: '2',
      email: 'jane.smith@example.com',
      name: 'Jane Smith',
      permission: 'view',
    },
  ]);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setEmail('');
      setPermission('view');
      setMessage('');
      setLinkCopied(false);
      setActiveTab('people');
    }
  }, [open]);

  const handleShareWithEmail = async () => {
    if (!email || !task) return;

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast({
        title: 'Invalid email',
        description: 'Please enter a valid email address.',
        variant: 'destructive',
      });
      return;
    }

    // Check if already shared
    if (sharedUsers.some((user) => user.email === email)) {
      toast({
        title: 'Already shared',
        description: 'This task is already shared with this user.',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      const newUser: ShareUser = {
        id: Date.now().toString(),
        email,
        permission,
      };

      setSharedUsers([...sharedUsers, newUser]);
      setEmail('');
      setMessage('');

      toast({
        title: 'Task shared',
        description: `Successfully shared task with ${email}`,
      });

      setIsLoading(false);
    }, 1000);
  };

  const handleUpdatePermission = (userId: string, newPermission: SharePermission) => {
    setSharedUsers(
      sharedUsers.map((user) =>
        user.id === userId ? { ...user, permission: newPermission } : user
      )
    );

    toast({
      title: 'Permission updated',
      description: 'User permission has been updated.',
    });
  };

  const handleRemoveUser = (userId: string) => {
    setSharedUsers(sharedUsers.filter((user) => user.id !== userId));

    toast({
      title: 'Access removed',
      description: 'User access has been removed.',
    });
  };

  const handleCopyLink = async () => {
    if (!task) return;

    // Generate a mock shareable link
    const shareableLink = `${window.location.origin}/shared/tasks/${task.id}`;

    try {
      await navigator.clipboard.writeText(shareableLink);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);

      toast({
        title: 'Link copied',
        description: 'Share link has been copied to clipboard.',
      });
    } catch (err) {
      toast({
        title: 'Failed to copy',
        description: 'Could not copy link to clipboard.',
        variant: 'destructive',
      });
    }
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      return name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return email?.charAt(0).toUpperCase() || '?';
  };

  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Share "{task.title}"</DialogTitle>
          <DialogDescription>
            Share this task with others or create a shareable link.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'people' | 'link')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="people">
              <Users className="mr-2 h-4 w-4" />
              People
            </TabsTrigger>
            <TabsTrigger value="link">
              <LinkIcon className="mr-2 h-4 w-4" />
              Link
            </TabsTrigger>
          </TabsList>

          <TabsContent value="people" className="space-y-4">
            {/* Share form */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <div className="flex gap-2">
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleShareWithEmail();
                      }
                    }}
                  />
                  <Select
                    value={permission}
                    onValueChange={(v) => setPermission(v as SharePermission)}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="view">
                        <div className="flex items-center gap-2">
                          <Eye className="h-4 w-4" />
                          <span>View</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="edit">
                        <div className="flex items-center gap-2">
                          <Edit2 className="h-4 w-4" />
                          <span>Edit</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message (optional)</Label>
                <Textarea
                  id="message"
                  placeholder="Add a message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  disabled={isLoading}
                  rows={3}
                />
              </div>

              <Button
                onClick={handleShareWithEmail}
                disabled={!email || isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sharing...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Send invite
                  </>
                )}
              </Button>
            </div>

            {/* Shared users list */}
            {sharedUsers.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">People with access</h4>
                <div className="space-y-2">
                  {sharedUsers.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback>{getInitials(user.name, user.email)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">{user.name || user.email}</p>
                          {user.name && (
                            <p className="text-xs text-muted-foreground">{user.email}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Select
                          value={user.permission}
                          onValueChange={(v) =>
                            handleUpdatePermission(user.id, v as SharePermission)
                          }
                        >
                          <SelectTrigger className="h-8 w-[100px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="view">View</SelectItem>
                            <SelectItem value="edit">Edit</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button variant="ghost" size="sm" onClick={() => handleRemoveUser(user.id)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="link" className="space-y-4">
            <div className="rounded-lg border p-4 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5" />
                  <div>
                    <p className="font-medium">Share via link</p>
                    <p className="text-sm text-muted-foreground">
                      Anyone with the link can {linkPermission} this task
                    </p>
                  </div>
                </div>
                <Switch checked={linkEnabled} onCheckedChange={setLinkEnabled} />
              </div>

              {linkEnabled && (
                <>
                  <div className="flex items-center gap-2">
                    <Select
                      value={linkPermission}
                      onValueChange={(v) => setLinkPermission(v as SharePermission)}
                    >
                      <SelectTrigger className="w-[120px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="view">
                          <div className="flex items-center gap-2">
                            <Eye className="h-4 w-4" />
                            <span>View only</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="edit">
                          <div className="flex items-center gap-2">
                            <Edit2 className="h-4 w-4" />
                            <span>Can edit</span>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={handleCopyLink} className="flex-1">
                      {linkCopied ? (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy link
                        </>
                      )}
                    </Button>
                  </div>

                  <Alert>
                    <Shield className="h-4 w-4" />
                    <AlertDescription>
                      Anyone with this link will be able to {linkPermission} this task. You can
                      disable the link at any time.
                    </AlertDescription>
                  </Alert>
                </>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
