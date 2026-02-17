import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Extract user-friendly error message from API response
 * Handles various error formats: field validation, detail messages, HTML errors, and raw errors
 */
export function extractErrorMessage(error: any): string {
  // Handle network errors
  if (!error.response) {
    if (error.code === 'ERR_NETWORK') {
      return 'Network error: Cannot reach the server. Please check your connection or try again later.';
    }
    if (error.message?.includes('ERR_CONNECTION')) {
      return 'Connection lost: The server is not responding. Please check if the server is running.';
    }
    return error.message || 'A network error occurred. Please try again.';
  }

  // Handle HTML error responses (backend returning error pages)
  if (typeof error.response.data === 'string' && error.response.data.includes('<!doctype html>')) {
    if (error.response.status >= 500) {
      return 'Server error (500): The server encountered an internal error. Please check the server logs or contact support.';
    }
    return `Server error (${error.response.status}): The request could not be processed.`;
  }

  // Handle JSON error responses
  if (error.response?.data && typeof error.response.data === 'object') {
    const data = error.response.data;
    
    // For server errors (5xx), provide helpful message
    if (error.response.status >= 500) {
      // Check for detail message first
      if (data.detail) {
        return `Server error: ${data.detail}`;
      }
      // Generic 500 error message
      return 'Server error. Please try again later or contact support if the problem persists.';
    }
    
    // Extract first field error (for validation errors)
    for (const [field, messages] of Object.entries(data)) {
      if (Array.isArray(messages) && messages.length > 0) {
        return `${field}: ${messages[0]}`;
      }
      if (typeof messages === 'string') {
        return `${field}: ${messages}`;
      }
    }
    
    // Fall back to detail field if present
    if (data.detail) {
      return data.detail;
    }
  }
  
  // Handle axios error message (e.g., "Request failed with status code 500")
  if (error.message) {
    return error.message;
  }
  
  // Generic fallback
  return 'An unexpected error occurred. Please try again.';
}
/**
 * Format ISO timestamp to readable time string
 * Examples: "2:30 PM", "Yesterday 3:45 PM", "Feb 10, 2:30 PM"
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  
  const diffTime = today.getTime() - messageDate.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  const timeStr = date.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
    hour12: true 
  });

  if (diffDays === 0) {
    return timeStr; // Same day: "2:30 PM"
  } else if (diffDays === 1) {
    return `Yesterday ${timeStr}`; // Yesterday: "Yesterday 2:30 PM"
  } else if (diffDays < 7) {
    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
    return `${dayName} ${timeStr}`; // Within a week: "Mon 2:30 PM"
  } else {
    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${dateStr} ${timeStr}`; // Older: "Feb 10, 2:30 PM"
  }
}