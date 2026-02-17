/**
 * Toast Notification Utility
 * Simple toast notification system for user feedback
 */

import React, { useEffect, useState } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

export interface ToastContextType {
  toasts: Toast[];
  addToast: (message: string, type: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

// Singleton instance for toast management
let toastInstance: ToastContextType | null = null;

/**
 * Simple toast notification system
 */
export function createToastManager(): ToastContextType {
  const toasts: Toast[] = [];
  const listeners: Set<(toasts: Toast[]) => void> = new Set();

  const notify = (toasts: Toast[]) => {
    listeners.forEach((listener) => listener(toasts));
  };

  return {
    toasts,
    addToast: (message: string, type: ToastType, duration = 3000) => {
      const id = Date.now().toString();
      const toast: Toast = { id, message, type, duration };
      
      toasts.push(toast);
      notify([...toasts]);

      if (duration > 0) {
        setTimeout(() => {
          const index = toasts.findIndex((t) => t.id === id);
          if (index !== -1) {
            toasts.splice(index, 1);
            notify([...toasts]);
          }
        }, duration);
      }

      return id;
    },
    removeToast: (id: string) => {
      const index = toasts.findIndex((t) => t.id === id);
      if (index !== -1) {
        toasts.splice(index, 1);
        notify([...toasts]);
      }
    },
    clearAll: () => {
      toasts.length = 0;
      notify([]);
    },
  };
}

/**
 * Hook to use toast notifications
 */
export function useToast() {
  if (!toastInstance) {
    toastInstance = createToastManager();
  }

  return {
    success: (message: string, duration?: number) =>
      toastInstance!.addToast(message, 'success', duration),
    error: (message: string, duration?: number) =>
      toastInstance!.addToast(message, 'error', duration),
    warning: (message: string, duration?: number) =>
      toastInstance!.addToast(message, 'warning', duration),
    info: (message: string, duration?: number) =>
      toastInstance!.addToast(message, 'info', duration),
    remove: (id: string) => toastInstance!.removeToast(id),
    clearAll: () => toastInstance!.clearAll(),
  };
}

/**
 * Toast Container Component
 */
export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    if (!toastInstance) {
      toastInstance = createToastManager();
    }

    const listener = (updatedToasts: Toast[]) => {
      setToasts([...updatedToasts]);
    };

    // Set initial toasts
    setToasts([...toastInstance.toasts]);
  }, []);

  const getToastStyles = (type: ToastType) => {
    const baseClass = 'px-4 py-3 rounded-lg font-medium text-white flex items-center gap-2';
    
    switch (type) {
      case 'success':
        return `${baseClass} bg-green-600`;
      case 'error':
        return `${baseClass} bg-red-600`;
      case 'warning':
        return `${baseClass} bg-yellow-600`;
      case 'info':
        return `${baseClass} bg-blue-600`;
      default:
        return baseClass;
    }
  };

  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return '';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${getToastStyles(toast.type)} shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-300 pointer-events-auto`}
        >
          <span className="text-lg">{getIcon(toast.type)}</span>
          <span>{toast.message}</span>
          <button
            onClick={() => toastInstance?.removeToast(toast.id)}
            className="ml-auto font-bold hover:opacity-80 transition-opacity"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
