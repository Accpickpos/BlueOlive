/**
 * API Error Handler Utility
 * Centralized error handling for API responses
 */

import { AxiosError } from 'axios';

export interface ApiError {
  statusCode: number;
  message: string;
  details?: Record<string, any>;
  isNetworkError: boolean;
  isValidationError: boolean;
  isAuthError: boolean;
  isNotFoundError: boolean;
  isServerError: boolean;
}

/**
 * Parse and standardize API errors
 */
export function parseApiError(error: unknown): ApiError {
  const defaultError: ApiError = {
    statusCode: 500,
    message: 'An unexpected error occurred',
    isNetworkError: false,
    isValidationError: false,
    isAuthError: false,
    isNotFoundError: false,
    isServerError: true,
  };

  if (!error) return defaultError;

  // Handle Axios errors
  if ((error as any).isAxiosError) {
    const axiosError = error as AxiosError;
    const status = axiosError.response?.status || 500;
    const data = axiosError.response?.data as any;

    return {
      statusCode: status,
      message: data?.detail || data?.message || axiosError.message || 'Unknown error',
      details: data?.errors || data,
      isNetworkError: !axiosError.response,
      isValidationError: status === 400 || status === 422,
      isAuthError: status === 401 || status === 403,
      isNotFoundError: status === 404,
      isServerError: status >= 500,
    };
  }

  // Handle Error objects
  if (error instanceof Error) {
    return {
      ...defaultError,
      message: error.message,
      isNetworkError: error.message.includes('Network'),
    };
  }

  // Handle string errors
  if (typeof error === 'string') {
    return {
      ...defaultError,
      message: error,
    };
  }

  return defaultError;
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  const apiError = parseApiError(error);

  if (apiError.isNetworkError) {
    return 'Network error. Please check your connection and try again.';
  }

  if (apiError.isAuthError) {
    return 'You do not have permission to perform this action. Please log in again.';
  }

  if (apiError.isNotFoundError) {
    return 'The requested resource was not found.';
  }

  if (apiError.isValidationError) {
    return apiError.message || 'Please check your input and try again.';
  }

  if (apiError.isServerError) {
    return 'Server error. Please try again later.';
  }

  return apiError.message || 'An unexpected error occurred';
}

/**
 * Get validation errors from API response
 */
export function getValidationErrors(error: unknown): Record<string, string> {
  const apiError = parseApiError(error);
  
  if (!apiError.isValidationError || !apiError.details) {
    return {};
  }

  const details = apiError.details;
  const errors: Record<string, string> = {};

  // Handle different error response formats
  if (typeof details === 'object') {
    Object.entries(details).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        errors[key] = value[0]?.message || value[0] || 'Invalid value';
      } else if (typeof value === 'object' && value !== null) {
        errors[key] = (value as any).message || JSON.stringify(value);
      } else {
        errors[key] = String(value);
      }
    });
  }

  return errors;
}

/**
 * Map API errors to form field errors
 */
export function mapApiErrorsToFormFields(
  error: unknown
): Record<string, string> {
  const validationErrors = getValidationErrors(error);
  const fieldErrorMap: Record<string, string> = {};

  // Map common API field names to form field names
  const fieldMapping: Record<string, string> = {
    debtor_account_number: 'debtorAccountNumber',
    account_number: 'accountNumber',
    cheque_number: 'chequeNumber',
    invoice_number: 'invoiceNumber',
    reference_number: 'referenceNumber',
    credit_note_date: 'creditNoteDate',
    job_date: 'jobDate',
    repair_date: 'repairDate',
    return_date: 'returnDate',
    cheque_date: 'chequeDate',
    opening_date: 'openingDate',
    closing_date: 'closingDate',
    line_items: 'lineItems',
  };

  Object.entries(validationErrors).forEach(([apiField, message]) => {
    const formField = fieldMapping[apiField] || apiField;
    fieldErrorMap[formField] = message;
  });

  return fieldErrorMap;
}

/**
 * Retry API request with exponential backoff
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error as Error;
      const apiError = parseApiError(error);

      // Don't retry on validation or auth errors
      if (
        apiError.isValidationError ||
        apiError.isAuthError ||
        apiError.isNotFoundError
      ) {
        throw error;
      }

      // Only retry on network errors or 5xx server errors
      if (apiError.isNetworkError || apiError.isServerError) {
        if (attempt < maxRetries - 1) {
          const delayMs = baseDelayMs * Math.pow(2, attempt);
          await new Promise((resolve) => setTimeout(resolve, delayMs));
          continue;
        }
      }

      throw error;
    }
  }

  throw lastError || new Error('Request failed after maximum retries');
}

/**
 * Common API error handler wrapper
 */
export function createApiErrorHandler(onError?: (error: ApiError) => void) {
  return (error: unknown) => {
    const apiError = parseApiError(error);
    onError?.(apiError);
    return apiError;
  };
}
