/**
 * API Error Handling Utilities
 * Comprehensive error handling for API calls
 */

export interface APIError {
  message: string;
  code?: string;
  details?: Record<string, string[]>;
}

export function handleAPIError(error: unknown): APIError {
  if (error instanceof Error) {
    // Handle Axios errors
    const axiosError = error as any;

    if (axiosError.response?.data) {
      const { data } = axiosError.response;

      return {
        message:
          data.detail ||
          data.message ||
          'An error occurred',
        code: data.code,
        details: data.errors || data,
      };
    }

    return {
      message: error.message,
      code: 'UNKNOWN_ERROR',
    };
  }

  return {
    message: 'An unknown error occurred',
    code: 'UNKNOWN_ERROR',
  };
}

export function getErrorMessage(error: unknown): string {
  const apiError = handleAPIError(error);

  if (apiError.details) {
    // Format field errors
    const messages = Object.entries(apiError.details).map(
      ([field, errors]) =>
        `${field}: ${(errors as string[]).join(', ')}`
    );
    return messages.join('; ');
  }

  return apiError.message;
}

// Common error codes and user-friendly messages
export const ERROR_MESSAGES: Record<string, string> = {
  ORDER_NOT_FOUND:
    'The requested purchase order could not be found.',
  INVALID_STATUS:
    'This action cannot be performed on the current order status.',
  SUPPLIER_NOT_FOUND:
    'The selected supplier could not be found.',
  STOCK_NOT_FOUND:
    'The stock item could not be found.',
  INSUFFICIENT_QUANTITY:
    'Insufficient quantity available.',
  DUPLICATE_ORDER:
    'A duplicate order number already exists.',
  PERMISSION_DENIED:
    'You do not have permission to perform this action.',
  VALIDATION_ERROR:
    'Please check your input and try again.',
};

export function getUserFriendlyError(error: unknown): string {
  const apiError = handleAPIError(error);
  const code = apiError.code || '';

  return ERROR_MESSAGES[code] || apiError.message;
}

/**
 * Format validation error details for display
 */
export function formatValidationErrors(
  details?: Record<string, string[]>
): string {
  if (!details) return '';

  const errors: string[] = [];
  for (const [field, messages] of Object.entries(details)) {
    const fieldName = field
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
    errors.push(`${fieldName}: ${(messages as string[]).join(', ')}`);
  }

  return errors.join('\n');
}

/**
 * Check if error is a specific type
 */
export function isAPIError(
  error: unknown,
  code: string
): boolean {
  const apiError = handleAPIError(error);
  return apiError.code === code;
}

/**
 * Create a user-friendly error message for common scenarios
 */
export function getContextualErrorMessage(
  error: unknown,
  context: string
): string {
  const apiError = handleAPIError(error);

  const contextMessages: Record<string, string> = {
    create: 'Failed to create purchase order',
    update: 'Failed to update purchase order',
    delete: 'Failed to delete purchase order',
    approve: 'Failed to approve purchase order',
    cancel: 'Failed to cancel purchase order',
    receipt: 'Failed to record goods receipt',
    search: 'Failed to search purchase orders',
  };

  const contextMessage = contextMessages[context] || 'Operation failed';
  return `${contextMessage}: ${apiError.message}`;
}
