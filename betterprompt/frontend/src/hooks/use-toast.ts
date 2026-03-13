import { useCallback, useEffect, useState } from 'react';
import type { ReactNode } from 'react';

export type ToastVariant = 'default' | 'success' | 'destructive' | 'warning' | 'info';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  action?: ReactNode;
  variant?: ToastVariant;
  duration?: number;
}

type ToastState = {
  toasts: Toast[];
};

const TOAST_LIMIT = 5;
const TOAST_DURATION = 5000;

let toastCount = 0;
let listeners: Array<(state: ToastState) => void> = [];
let memoryState: ToastState = { toasts: [] };

function dispatch(action: { type: 'ADD' | 'REMOVE' | 'REMOVE_ALL'; toast?: Toast; toastId?: string }) {
  switch (action.type) {
    case 'ADD':
      if (action.toast) {
        memoryState = {
          toasts: [action.toast, ...memoryState.toasts].slice(0, TOAST_LIMIT),
        };
      }
      break;
    case 'REMOVE':
      memoryState = {
        toasts: memoryState.toasts.filter((t) => t.id !== action.toastId),
      };
      break;
    case 'REMOVE_ALL':
      memoryState = { toasts: [] };
      break;
  }
  listeners.forEach((listener) => listener(memoryState));
}

function genId() {
  toastCount = (toastCount + 1) % Number.MAX_SAFE_INTEGER;
  return toastCount.toString();
}

function toast(props: Omit<Toast, 'id'>) {
  const id = genId();
  const duration = props.duration ?? TOAST_DURATION;

  dispatch({
    type: 'ADD',
    toast: { ...props, id },
  });

  if (duration > 0) {
    setTimeout(() => {
      dispatch({ type: 'REMOVE', toastId: id });
    }, duration);
  }

  return {
    id,
    dismiss: () => dispatch({ type: 'REMOVE', toastId: id }),
  };
}

function useToast() {
  const [state, setState] = useState<ToastState>(memoryState);

  useEffect(() => {
    listeners.push(setState);
    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }, []);

  const dismiss = useCallback((toastId?: string) => {
    if (toastId) {
      dispatch({ type: 'REMOVE', toastId });
    } else {
      dispatch({ type: 'REMOVE_ALL' });
    }
  }, []);

  return {
    ...state,
    toast,
    dismiss,
  };
}

type ToastInput = string | Omit<Toast, 'id' | 'variant'>;
const normalizeInput = (input: ToastInput): Omit<Toast, 'id' | 'variant'> =>
  typeof input === 'string' ? { description: input } : input;

toast.success = (input: ToastInput) => toast({ ...normalizeInput(input), variant: 'success' });
toast.error = (input: ToastInput) => toast({ ...normalizeInput(input), variant: 'destructive' });
toast.warning = (input: ToastInput) => toast({ ...normalizeInput(input), variant: 'warning' });
toast.info = (input: ToastInput) => toast({ ...normalizeInput(input), variant: 'info' });

export { useToast, toast };
