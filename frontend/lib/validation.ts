/**
 * Form Validation Utilities
 * Standard validation rules and error handling for forms across the application
 */

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export interface ValidationRule {
  required?: boolean | string;
  minLength?: { value: number; message: string };
  maxLength?: { value: number; message: string };
  pattern?: { value: RegExp; message: string };
  custom?: (value: any) => string | null;
}

export interface FormValidationRules {
  [fieldName: string]: ValidationRule;
}

/**
 * Standard validation patterns
 */
export const ValidationPatterns = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^(\+27|0)[0-9]{9,}$/,
  ACCOUNT_NUMBER: /^[A-Za-z0-9\-]+$/,
  NUMERIC: /^[0-9]+$/,
  DECIMAL: /^[0-9]+(\.[0-9]{1,2})?$/,
  DATE: /^\d{4}-\d{2}-\d{2}$/,
  CHEQUE_NUMBER: /^[0-9]{6,10}$/,
  VAT_NUMBER: /^[0-9]{10}$/,
};

/**
 * Standard validation messages
 */
export const ValidationMessages = {
  REQUIRED: 'This field is required',
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_PHONE: 'Please enter a valid phone number',
  INVALID_ACCOUNT: 'Please enter a valid account number',
  INVALID_NUMERIC: 'Please enter a valid number',
  INVALID_DECIMAL: 'Please enter a valid decimal number',
  INVALID_DATE: 'Please enter a valid date (YYYY-MM-DD)',
  INVALID_CHEQUE: 'Please enter a valid cheque number',
  INVALID_VAT: 'Please enter a valid VAT number',
  MIN_LENGTH: (min: number) => `Minimum ${min} characters required`,
  MAX_LENGTH: (max: number) => `Maximum ${max} characters allowed`,
};

/**
 * Validate a single field value against a rule
 */
export function validateField(
  value: any,
  rule: ValidationRule,
  fieldName: string
): string | null {
  // Check required
  if (rule.required) {
    if (value === undefined || value === null || value === '') {
      return typeof rule.required === 'string'
        ? rule.required
        : ValidationMessages.REQUIRED;
    }
  }

  // Skip further validation if value is empty and not required
  if (!rule.required && (value === undefined || value === null || value === '')) {
    return null;
  }

  // Check min length
  if (rule.minLength && value.length < rule.minLength.value) {
    return rule.minLength.message;
  }

  // Check max length
  if (rule.maxLength && value.length > rule.maxLength.value) {
    return rule.maxLength.message;
  }

  // Check pattern
  if (rule.pattern && !rule.pattern.value.test(value)) {
    return rule.pattern.message;
  }

  // Check custom validation
  if (rule.custom) {
    const error = rule.custom(value);
    if (error) return error;
  }

  return null;
}

/**
 * Validate entire form object against rules
 */
export function validateForm(
  data: Record<string, any>,
  rules: FormValidationRules
): ValidationResult {
  const errors: Record<string, string> = {};

  Object.entries(rules).forEach(([fieldName, rule]) => {
    const error = validateField(data[fieldName], rule, fieldName);
    if (error) {
      errors[fieldName] = error;
    }
  });

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Predefined validation rules for common fields
 */
export const CommonValidationRules = {
  accountNumber: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.ACCOUNT_NUMBER,
      message: ValidationMessages.INVALID_ACCOUNT,
    },
  }),

  email: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.EMAIL,
      message: ValidationMessages.INVALID_EMAIL,
    },
  }),

  phone: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.PHONE,
      message: ValidationMessages.INVALID_PHONE,
    },
  }),

  amount: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.DECIMAL,
      message: ValidationMessages.INVALID_DECIMAL,
    },
    custom: (value) => {
      if (typeof value === 'string') {
        const num = parseFloat(value);
        if (isNaN(num)) return ValidationMessages.INVALID_DECIMAL;
        if (num < 0) return 'Amount cannot be negative';
      }
      return null;
    },
  }),

  date: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.DATE,
      message: ValidationMessages.INVALID_DATE,
    },
  }),

  chequeNumber: (required = true): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    pattern: {
      value: ValidationPatterns.CHEQUE_NUMBER,
      message: ValidationMessages.INVALID_CHEQUE,
    },
  }),

  text: (required = true, minLength = 0, maxLength = 255): ValidationRule => ({
    required: required ? ValidationMessages.REQUIRED : false,
    minLength:
      minLength > 0
        ? {
            value: minLength,
            message: ValidationMessages.MIN_LENGTH(minLength),
          }
        : undefined,
    maxLength: {
      value: maxLength,
      message: ValidationMessages.MAX_LENGTH(maxLength),
    },
  }),
};

/**
 * Format validation errors for display
 */
export function formatValidationErrors(
  errors: Record<string, string>
): string {
  const errorList = Object.entries(errors)
    .map(([field, message]) => `${field}: ${message}`)
    .join('\n');
  return errorList;
}
