'use client';

import { useEffect, ReactNode } from 'react';

interface ChunkErrorHandlerProps {
  children: ReactNode;
}

export function ChunkErrorHandler({ children }: ChunkErrorHandlerProps) {
  useEffect(() => {
    // Handle ChunkLoadError - occurs when chunks are updated during dev
    const handleError = (event: ErrorEvent) => {
      if (
        event.message &&
        (event.message.includes('ChunkLoadError') ||
          event.message.includes('Failed to fetch dynamically imported module') ||
          event.message.includes('Loading chunk'))
      ) {
        console.warn('Chunk load error detected, reloading page...');
        window.location.reload();
      }
    };

    // Also handle unhandled promise rejections that might be chunk-related
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      if (
        reason &&
        typeof reason === 'string' &&
        (reason.includes('ChunkLoadError') ||
          reason.includes('Failed to fetch dynamically imported module'))
      ) {
        console.warn('Chunk load error in promise, reloading page...');
        window.location.reload();
      }
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return <>{children}</>;
}
