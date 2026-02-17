/**
 * Error Boundary Component
 * Catches errors in child components and displays a fallback UI
 */

'use client';

import React, { ErrorInfo, ReactNode, useState } from 'react';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('Error caught by boundary:', error, errorInfo);
    
    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError);
      }

      return (
        <div className="flex items-center justify-center min-h-[400px] p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <h1 className="text-lg font-bold text-red-900 mb-2">
              ⚠️ Something went wrong
            </h1>
            <p className="text-red-800 text-sm mb-4">
              {this.state.error.message}
            </p>
            <details className="mb-4">
              <summary className="text-sm text-red-700 cursor-pointer font-medium">
                Error details
              </summary>
              <pre className="text-xs text-red-600 mt-2 overflow-auto bg-white p-2 border border-red-100 rounded">
                {this.state.error.stack}
              </pre>
            </details>
            <button
              onClick={this.resetError}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm font-medium"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
