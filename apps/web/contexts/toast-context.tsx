'use client';

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { Toast, ToastContainer, ToastProps } from '@/components/ui/toast';

interface ToastContextState {
  toasts: ToastProps[];
}

type ToastAction = { type: 'ADD_TOAST'; toast: ToastProps } | { type: 'REMOVE_TOAST'; id: string };

const ToastContext = createContext<{
  state: ToastContextState;
  dispatch: React.Dispatch<ToastAction>;
  toast: (props: Omit<ToastProps, 'id'>) => void;
  dismiss: (id: string) => void;
} | null>(null);

function toastReducer(state: ToastContextState, action: ToastAction): ToastContextState {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [...state.toasts, action.toast],
      };
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter((toast) => toast.id !== action.id),
      };
    default:
      return state;
  }
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(toastReducer, { toasts: [] });

  const toast = useCallback(
    (props: Omit<ToastProps, 'id'>) => {
      const id = Math.random().toString(36).substr(2, 9);
      const newToast: ToastProps = {
        ...props,
        id,
        duration: props.duration ?? 5000,
      };

      dispatch({ type: 'ADD_TOAST', toast: newToast });

      // Auto dismiss after duration
      if (newToast.duration > 0) {
        setTimeout(() => {
          dispatch({ type: 'REMOVE_TOAST', id });
        }, newToast.duration);
      }
    },
    [dispatch]
  );

  const dismiss = useCallback(
    (id: string) => {
      dispatch({ type: 'REMOVE_TOAST', id });
    },
    [dispatch]
  );

  return (
    <ToastContext.Provider value={{ state, dispatch, toast, dismiss }}>
      {children}
      <ToastContainer>
        {state.toasts.map((toastProps) => (
          <Toast key={toastProps.id} {...toastProps} onDismiss={dismiss} />
        ))}
      </ToastContainer>
    </ToastContext.Provider>
  );
}

export function useToastContext() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
}
