import { useToastContext } from '@/contexts/toast-context';

export function useToast() {
  const { toast: showToast } = useToastContext();

  const toast = (options: {
    title?: string;
    description?: string;
    variant?: 'default' | 'destructive';
    duration?: number;
  }) => {
    showToast(options);
  };

  return { toast };
}
