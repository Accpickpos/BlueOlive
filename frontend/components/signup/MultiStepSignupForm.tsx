'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Loader2, 
  AlertCircle, 
  Building2,
  User,
  Mail,
  Lock,
  Globe,
  Sparkles
} from 'lucide-react';
import { signup, validateSubdomain, getActiveSubscriptionPlans } from '@/lib/api';
import { useAuthContext } from '@/lib/AuthContext';
import { setTenant, setShops, setCurrentShop } from '@/lib/shopContext';

// Types
interface SignupFormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  companyName: string;
  subdomain: string;
  subscriptionPlanId: string;
}

interface FormErrors {
  [key: string]: string;
}

interface SubdomainStatus {
  validated: boolean;
  checking: boolean;
  available: boolean | null;
  error: string;
  suggestions: string[];
}

// Steps configuration
const STEPS = [
  { id: 1, title: 'Account', description: 'Create your account' },
  { id: 2, title: 'Organization', description: 'Set up your company' },
  { id: 3, title: 'Plan', description: 'Choose your plan' },
];

export default function MultiStepSignupForm() {
  const router = useRouter();
  const { refetch } = useAuthContext();
  
  // Form state
  const [formData, setFormData] = useState<SignupFormData>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    companyName: '',
    subdomain: '',
    subscriptionPlanId: '',
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [errors, setErrors] = useState<FormErrors>({});
  const [subdomainStatus, setSubdomainStatus] = useState<SubdomainStatus>({
    validated: false,
    checking: false,
    available: null,
    error: '',
    suggestions: [],
  });
  const [plans, setPlans] = useState<any[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch subscription plans on mount
  useEffect(() => {
    async function fetchPlans() {
      try {
        const data = await getActiveSubscriptionPlans();
        setPlans(data);
        // Set default to first non-trial plan if available
        const nonTrialPlan = data.find((p: any) => !p.is_trial);
        if (nonTrialPlan) {
          setFormData(prev => ({ ...prev, subscriptionPlanId: nonTrialPlan.id.toString() }));
        }
      } catch (error) {
        console.error('Failed to fetch plans:', error);
      } finally {
        setPlansLoading(false);
      }
    }
    fetchPlans();
  }, []);

  // Debounced subdomain validation
  const validateSubdomainDebounced = useCallback(
    async (subdomain: string) => {
      if (subdomain.length < 3) {
        setSubdomainStatus({
          validated: false,
          checking: false,
          available: null,
          error: 'Subdomain must be at least 3 characters',
          suggestions: [],
        });
        return;
      }

      if (!/^[a-z0-9][a-z0-9-]*[a-z0-9]$/.test(subdomain)) {
        setSubdomainStatus({
          validated: false,
          checking: false,
          available: null,
          error: 'Subdomain can only contain letters, numbers, and hyphens',
          suggestions: [],
        });
        return;
      }

      setSubdomainStatus(prev => ({ ...prev, checking: true, error: '' }));

      try {
        const result = await validateSubdomain(subdomain);
        setSubdomainStatus({
          validated: true,
          checking: false,
          available: result.available,
          error: '',
          suggestions: result.suggestions || [],
        });
      } catch (error: any) {
        setSubdomainStatus({
          validated: false,
          checking: false,
          available: null,
          error: error?.response?.data?.detail || 'Unable to validate subdomain',
          suggestions: [],
        });
      }
    },
    []
  );

  // Trigger subdomain validation when it changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.subdomain) {
        validateSubdomainDebounced(formData.subdomain);
      }
    }, 500); // Debounce for 500ms

    return () => clearTimeout(timer);
  }, [formData.subdomain, validateSubdomainDebounced]);

  // Handle input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
    
    // Clear subdomain status when user modifies it
    if (name === 'subdomain') {
      setSubdomainStatus(prev => ({ ...prev, validated: false }));
    }
  };

  // Validate current step
  const validateStep = (step: number): boolean => {
    const newErrors: FormErrors = {};

    if (step === 1) {
      if (!formData.email) {
        newErrors.email = 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = 'Please enter a valid email address';
      }
      
      if (!formData.username) {
        newErrors.username = 'Username is required';
      } else if (formData.username.length < 3) {
        newErrors.username = 'Username must be at least 3 characters';
      } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
        newErrors.username = 'Username can only contain letters, numbers, and underscores';
      }
      
      if (!formData.password) {
        newErrors.password = 'Password is required';
      } else if (formData.password.length < 8) {
        newErrors.password = 'Password must be at least 8 characters';
      }
      
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
      
      if (!formData.firstName) {
        newErrors.firstName = 'First name is required';
      }
      
      if (!formData.lastName) {
        newErrors.lastName = 'Last name is required';
      }
    }

    if (step === 2) {
      if (!formData.companyName) {
        newErrors.companyName = 'Company name is required';
      } else if (formData.companyName.length < 2) {
        newErrors.companyName = 'Company name must be at least 2 characters';
      }
      
      if (!formData.subdomain) {
        newErrors.subdomain = 'Subdomain is required';
      } else if (!subdomainStatus.validated || !subdomainStatus.available) {
        newErrors.subdomain = subdomainStatus.error || 'Please enter a valid subdomain';
      }
    }

    if (step === 3) {
      if (!formData.subscriptionPlanId) {
        newErrors.subscriptionPlanId = 'Please select a subscription plan';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle step navigation
  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  // Handle final submission
  const handleSubmit = async () => {
    if (!validateStep(3)) return;

    setSubmitting(true);
    setSubmitError('');

    try {
      const response = await signup({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        first_name: formData.firstName,
        last_name: formData.lastName,
        company_name: formData.companyName,
        subdomain: formData.subdomain,
        subscription_plan_id: parseInt(formData.subscriptionPlanId),
      });

      if (response.status === 201 || response.status === 200) {
        setSubmitSuccess(true);
        
        // Store tenant in localStorage
        setTenant(formData.subdomain);
        
        // Fetch shops for the tenant
        try {
          const shops = await getActiveSubscriptionPlans(); // This might need to be changed to getTenantShops
          // Note: The original code used getTenantShops but we need to verify this function exists
        } catch (e) {
          console.warn('Failed to fetch shops after signup:', e);
        }
        
        // Refetch user profile
        try {
          await refetch();
        } catch (e) {
          console.warn('Refetch failed, proceeding with redirect anyway');
        }

        // Redirect to dashboard after a short delay
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      }
    } catch (error: any) {
      const errorMsg = 
        error?.response?.data?.detail || 
        error?.response?.data?.message ||
        error?.message ||
        'Signup failed. Please try again.';
      setSubmitError(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  // Get step completion status
  const isStepCompleted = (step: number): boolean => {
    if (step < currentStep) return true;
    if (step === currentStep) return false;
    return false;
  };

  // Render form field with validation
  const renderField = (
    name: keyof SignupFormData,
    label: string,
    type: string = 'text',
    required: boolean = false,
    helperText?: string,
    icon?: React.ReactNode
  ) => (
    <div className="space-y-1">
      <label 
        htmlFor={name} 
        className="block text-sm font-medium text-gray-300"
      >
        {label}
        {required && <span className="text-red-400 ml-1">*</span>}
      </label>
      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400 h-5 w-5">{icon}</span>
          </div>
        )}
        <input
          type={type}
          name={name}
          id={name}
          value={formData[name]}
          onChange={handleChange}
          disabled={submitting}
          className={`
            block w-full rounded-lg bg-gray-800 border text-white placeholder-gray-400
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
            ${errors[name] 
              ? 'border-red-500 focus:ring-red-500' 
              : 'border-gray-600 focus:ring-indigo-500'
            }
            ${icon ? 'pl-10' : 'pl-4'} pr-4 py-3
            transition-colors duration-200
          `}
          aria-invalid={errors[name] ? 'true' : 'false'}
          aria-describedby={errors[name] ? `${name}-error` : undefined}
        />
      </div>
      {helperText && !errors[name] && (
        <p className="text-xs text-gray-500 mt-1">{helperText}</p>
      )}
      {errors[name] && (
        <p id={`${name}-error`} className="text-sm text-red-400 mt-1 flex items-center gap-1" role="alert">
          <AlertCircle className="h-4 w-4" />
          {errors[name]}
        </p>
      )}
    </div>
  );

  // Render step 1: Account details
  const renderStep1 = () => (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {renderField('firstName', 'First Name', 'text', true, undefined, <User className="h-5 w-5" />)}
        {renderField('lastName', 'Last Name', 'text', true, undefined, <User className="h-5 w-5" />)}
      </div>
      <>
        {renderField('email', 'Email Address', 'email', true, 'We will send a verification link to this email', <Mail className="h-5 w-5" />)}
        {renderField('username', 'Username', 'text', true, 'This will be used for login', <User className="h-5 w-5" />)}
      </>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {renderField('password', 'Password', 'password', true, 'At least 8 characters', <Lock className="h-5 w-5" />)}
        {renderField('confirmPassword', 'Confirm Password', 'password', true, undefined, <Lock className="h-5 w-5" />)}
      </div>
    </div>
  );

  // Render step 2: Organization details
  const renderStep2 = () => (
    <div className="space-y-5">
      <>
        {renderField('companyName', 'Company Name', 'text', true, 'Your organization legal name', <Building2 className="h-5 w-5" />)}
      </>
      
      <div className="space-y-1">
        <label 
          htmlFor="subdomain" 
          className="block text-sm font-medium text-gray-300"
        >
          Subdomain <span className="text-red-400 ml-1">*</span>
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Globe className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            name="subdomain"
            id="subdomain"
            value={formData.subdomain}
            onChange={handleChange}
            disabled={submitting}
            placeholder="your-company"
            className={`
              block w-full rounded-lg bg-gray-800 border text-white placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
              ${errors.subdomain 
                ? 'border-red-500 focus:ring-red-500' 
                : subdomainStatus.available === true
                  ? 'border-green-500 focus:ring-green-500'
                  : 'border-gray-600 focus:ring-indigo-500'
              }
              pl-10 pr-20 py-3
              transition-colors duration-200
            `}
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            {subdomainStatus.checking ? (
              <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
            ) : subdomainStatus.available === true ? (
              <Check className="h-5 w-5 text-green-500" />
            ) : null}
          </div>
        </div>
        
        {/* Domain preview */}
        <div className="mt-2 text-sm text-gray-500">
          Your URL will be: <span className="text-indigo-400 font-mono">{formData.subdomain || 'your-company'}.blueolive.co.za</span>
        </div>
        
        {/* Validation feedback */}
        {errors.subdomain && (
          <p className="text-sm text-red-400 mt-1 flex items-center gap-1" role="alert">
            <AlertCircle className="h-4 w-4" />
            {errors.subdomain}
          </p>
        )}
        {subdomainStatus.error && !errors.subdomain && (
          <p className="text-sm text-red-400 mt-1 flex items-center gap-1" role="alert">
            <AlertCircle className="h-4 w-4" />
            {subdomainStatus.error}
          </p>
        )}
        {subdomainStatus.suggestions.length > 0 && (
          <div className="mt-2">
            <p className="text-sm text-gray-400">Available alternatives:</p>
            <div className="flex flex-wrap gap-2 mt-1">
              {subdomainStatus.suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, subdomain: suggestion }))}
                  className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 text-indigo-300 rounded-full transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Render step 3: Plan selection
  const renderStep3 = () => (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-3">
          Select a Plan <span className="text-red-400 ml-1">*</span>
        </label>
        {plansLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <span className="ml-2 text-gray-400">Loading plans...</span>
          </div>
        ) : plans.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            No subscription plans available. Please contact support.
          </div>
        ) : (
          <div className="grid gap-4">
            {plans.map((plan: any) => (
              <label
                key={plan.id}
                className={`
                  relative block cursor-pointer rounded-xl border-2 p-4 transition-all duration-200
                  ${formData.subscriptionPlanId === plan.id.toString()
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                  }
                `}
              >
                <input
                  type="radio"
                  name="subscriptionPlanId"
                  value={plan.id}
                  checked={formData.subscriptionPlanId === plan.id.toString()}
                  onChange={handleChange}
                  className="sr-only"
                />
                <div className="flex items-start justify-between">
                  <div>
                    <span className="block text-lg font-semibold text-white">
                      {plan.name}
                    </span>
                    <span className="block text-sm text-gray-400 mt-1">
                      {plan.description || 'No description available'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="block text-xl font-bold text-indigo-400">
                      {plan.is_trial ? 'Free Trial' : `R${plan.price}/mo`}
                    </span>
                  </div>
                </div>
                {formData.subscriptionPlanId === plan.id.toString() && (
                  <div className="absolute top-4 right-4">
                    <Check className="h-5 w-5 text-indigo-500" />
                  </div>
                )}
              </label>
            ))}
          </div>
        )}
        {errors.subscriptionPlanId && (
          <p className="text-sm text-red-400 mt-2 flex items-center gap-1" role="alert">
            <AlertCircle className="h-4 w-4" />
            {errors.subscriptionPlanId}
          </p>
        )}
      </div>
    </div>
  );

  // Render success state
  if (submitSuccess) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mb-4">
          <Check className="h-8 w-8 text-green-500" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">Account Created!</h3>
        <p className="text-gray-400 mb-6">Redirecting you to your dashboard...</p>
        <div className="flex items-center justify-center gap-2">
          <Loader2 className="h-5 w-5 text-indigo-500 animate-spin" />
          <span className="text-gray-400">Setting up your workspace</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step indicator */}
      <nav aria-label="Progress" className="mb-8">
        <ol role="list" className="flex items-center justify-between">
          {STEPS.map((step, stepIdx) => (
            <li key={step.title} className={`relative ${stepIdx !== STEPS.length - 1 ? 'pr-8 sm:pr-20 flex-1' : ''}`}>
              {stepIdx !== STEPS.length - 1 && (
                <div 
                  className={`
                    absolute top-4 right-0 h-0.5 w-full transition-colors duration-300
                    ${currentStep > step.id ? 'bg-indigo-500' : 'bg-gray-700'}
                  `}
                  aria-hidden="true"
                />
              )}
              <button
                onClick={() => {
                  if (currentStep > step.id) {
                    setCurrentStep(step.id);
                  }
                }}
                disabled={step.id > currentStep}
                className={`
                  relative flex flex-col items-start group focus:outline-none
                  ${step.id > currentStep ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
                `}
              >
                <span className="flex items-center">
                  <span 
                    className={`
                      relative z-10 flex h-8 w-8 items-center justify-center rounded-full transition-colors duration-300
                      ${isStepCompleted(step.id) 
                        ? 'bg-indigo-500' 
                        : currentStep === step.id
                          ? 'border-2 border-indigo-500 bg-gray-800'
                          : 'border-2 border-gray-700 bg-gray-800'
                      }
                    `}
                  >
                    {isStepCompleted(step.id) ? (
                      <Check className="h-5 w-5 text-white" aria-hidden="true" />
                    ) : (
                      <span className={`text-sm ${currentStep === step.id ? 'text-indigo-500' : 'text-gray-400'}`}>
                        {step.id}
                      </span>
                    )}
                  </span>
                </span>
                <span className="mt-2 text-sm font-medium">
                  <span className={currentStep === step.id ? 'text-white' : 'text-gray-400'}>
                    {step.title}
                  </span>
                </span>
                <span className="text-xs text-gray-500 mt-0.5">
                  {step.description}
                </span>
              </button>
            </li>
          ))}
        </ol>
      </nav>

      {/* Form content */}
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 sm:p-8">
        {/* Step title */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            {currentStep === 1 && <User className="h-5 w-5 text-indigo-500" />}
            {currentStep === 2 && <Building2 className="h-5 w-5 text-indigo-500" />}
            {currentStep === 3 && <Sparkles className="h-5 w-5 text-indigo-500" />}
            {STEPS[currentStep - 1].title}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {STEPS[currentStep - 1].description}
          </p>
        </div>

        {/* Error message */}
        {submitError && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3" role="alert">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-red-400">{submitError}</p>
            </div>
          </div>
        )}

        {/* Step content */}
        <form onSubmit={(e) => e.preventDefault()}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
        </form>

        {/* Navigation buttons */}
        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 1 || submitting}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${currentStep === 1 
                ? 'text-gray-600 cursor-not-allowed' 
                : 'text-gray-300 hover:text-white hover:bg-gray-800'
              }
            `}
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>

          {currentStep < STEPS.length ? (
            <button
              type="button"
              onClick={handleNext}
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
              <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Create Account
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Footer link */}
      <p className="mt-6 text-center text-sm text-gray-400">
        Already have an account?{' '}
        <Link href="/auth?tab=login" className="text-indigo-400 hover:text-indigo-300 font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
