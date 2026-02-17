'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Loader, AlertCircle, CheckCircle } from 'lucide-react';

import type { DebtorAccount, DebtorCreateData, DebtorEditData } from '@/lib/types/debtors';

interface DebtorAccountFormProps {
  initialData?: DebtorAccount;
  isEdit?: boolean;
  onSuccess?: () => void;
}

// Constants
const SUCCESS_REDIRECT_DELAY = 2000;
const MAX_SHORT_NAME_LENGTH = 20;
const MAX_CONTACT_LENGTH = 20;
const MAX_POSTAL_CODE_LENGTH = 4;

const DEFAULT_FORM_DATA: DebtorCreateData = {
  dno: '',
  dname: '',
  dsname: '',
  dcontact: '',
  dtel: '',
  dfax: '',
  dadd1: '',
  dadd2: '',
  dadd3: '',
  dpcode: '',
  delad1: '',
  delad2: '',
  delad3: '',
  delad4: '',
  dtaxno: '',
  acctype: '',
  price: 1,
  terms: 30,
  ddiscper: 0,
  pdisc: 0,
  dclimit: 0,
  darea: 0,
  dintflag: false,
  blockflag: false,
  is_active: true,
  discprn: false,
  dposbal: 0,
};

type FormData = DebtorCreateData & Partial<Pick<DebtorAccount, 'id' | 'created_at' | 'updated_at'>>;

export default function DebtorAccountForm({
  initialData,
  isEdit = false,
  onSuccess,
}: DebtorAccountFormProps) {
  const [formData, setFormData] = useState<FormData>(DEFAULT_FORM_DATA);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Sync formData when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData({
        ...DEFAULT_FORM_DATA,
        ...initialData,
        // Normalize boolean flags from API ('Y'/'N' or true/false to boolean)
        dintflag: initialData.dintflag === 'Y' || initialData.dintflag === true,
        blockflag: initialData.blockflag === 'Y' || initialData.blockflag === true,
      });
    }
  }, [initialData]);

  const mutation = useMutation({
    mutationFn: async () => {
      // Prepare data for API submission
      const submitData = prepareSubmitData(formData, isEdit);
      
      if (isEdit && initialData?.id) {
        return debtorsApi.accounts.update(initialData.id, submitData as DebtorEditData);
      } else {
        return debtorsApi.accounts.create(submitData as DebtorCreateData);
      }
    },
    onSuccess: () => {
      setSuccess(true);
      setError(null);
      setTimeout(() => {
        onSuccess?.();
      }, SUCCESS_REDIRECT_DELAY);
    },
    onError: (err: any) => {
      const errorData = err.response?.data;
      if (typeof errorData === 'object' && errorData !== null && !errorData.detail) {
        // Handle field-specific validation errors
        const fieldErrors = Object.entries(errorData)
          .map(([field, message]) => `${field}: ${message}`)
          .join(', ');
        setError(fieldErrors || 'Failed to save account');
      } else {
        setError(errorData?.detail || err.message || 'Failed to save account');
      }
      setSuccess(false);
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    let processedValue: any = value;
    
    if (type === 'checkbox') {
      processedValue = (e.target as HTMLInputElement).checked;
    } else if (type === 'number') {
      // Convert to number, handle empty string
      processedValue = value === '' ? 0 : Number(value);
    }
    
    setFormData((prev) => ({
      ...prev,
      [name]: processedValue,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    const validationError = validateForm(formData);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div 
          className="p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2"
          role="alert"
          aria-live="assertive"
        >
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Success Alert */}
      {success && (
        <div 
          className="p-3 bg-green-50 border border-green-200 rounded-lg flex gap-2"
          role="alert"
          aria-live="polite"
        >
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-green-800">
            {isEdit ? 'Account updated successfully!' : 'Account created successfully!'}
          </div>
        </div>
      )}

      <div className="space-y-8">
        {/* Basic Information Section */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dno" className="block text-sm font-medium mb-1">
                  Account Number
                </label>
                <Input
                  id="dno"
                  name="dno"
                  value={formData.dno || ''}
                  onChange={handleChange}
                  placeholder="Auto-generated"
                  disabled={isEdit}
                  aria-describedby="dno-hint"
                />
                <p id="dno-hint" className="text-xs text-gray-500 mt-1">
                  {isEdit ? 'Cannot be changed' : 'Will be assigned automatically'}
                </p>
              </div>
              
              <div>
                <label htmlFor="dname" className="block text-sm font-medium mb-1">
                  <span className="text-red-600">* </span>Debtor Name
                </label>
                <Input
                  id="dname"
                  name="dname"
                  value={formData.dname || ''}
                  onChange={handleChange}
                  placeholder="Company name"
                  required
                  aria-required="true"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dsname" className="block text-sm font-medium mb-1">
                  <span className="text-red-600">* </span>Short Name
                </label>
                <Input
                  id="dsname"
                  name="dsname"
                  value={formData.dsname || ''}
                  onChange={handleChange}
                  placeholder="Max 20 characters"
                  maxLength={MAX_SHORT_NAME_LENGTH}
                  required
                  aria-required="true"
                  disabled={mutation.isPending}
                />
              </div>
              
              <div>
                <label htmlFor="acctype" className="block text-sm font-medium mb-1">
                  Account Type
                </label>
                <select
                  id="acctype"
                  name="acctype"
                  value={formData.acctype || ''}
                  onChange={handleChange}
                  className="w-full border rounded-md px-3 py-2 h-10 text-sm"
                  disabled={mutation.isPending}
                >
                  <option value="">Balance Forward</option>
                  <option value="O">Open Item</option>
                  <option value="C">Cash Customer</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="dcontact" className="block text-sm font-medium mb-1">
                Contact Person
              </label>
              <Input
                id="dcontact"
                name="dcontact"
                value={formData.dcontact || ''}
                onChange={handleChange}
                placeholder="e.g., John Smith, Jane Doe"
                maxLength={MAX_CONTACT_LENGTH}
                aria-describedby="dcontact-hint"
                disabled={mutation.isPending}
              />
              <p id="dcontact-hint" className="text-xs text-gray-500 mt-1">
                The person to ask for when calling about orders or payments
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dtel" className="block text-sm font-medium mb-1">
                  Telephone
                </label>
                <Input
                  id="dtel"
                  name="dtel"
                  type="tel"
                  value={formData.dtel || ''}
                  onChange={handleChange}
                  placeholder="Primary phone"
                  disabled={mutation.isPending}
                />
              </div>
              
              <div>
                <label htmlFor="dfax" className="block text-sm font-medium mb-1">
                  Fax
                </label>
                <Input
                  id="dfax"
                  name="dfax"
                  type="tel"
                  value={formData.dfax || ''}
                  onChange={handleChange}
                  placeholder="Fax number"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dtaxno" className="block text-sm font-medium mb-1">
                  Tax/VAT Number
                </label>
                <Input
                  id="dtaxno"
                  name="dtaxno"
                  value={formData.dtaxno || ''}
                  onChange={handleChange}
                  placeholder="VAT registration"
                  disabled={mutation.isPending}
                />
              </div>
              
              <div>
                <label htmlFor="dpcode" className="block text-sm font-medium mb-1">
                  Postal Code
                </label>
                <Input
                  id="dpcode"
                  name="dpcode"
                  value={formData.dpcode || ''}
                  onChange={handleChange}
                  placeholder="Postal code"
                  maxLength={MAX_POSTAL_CODE_LENGTH}
                  disabled={mutation.isPending}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Addresses Section */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Addresses</h2>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-bold mb-3 text-gray-700">Postal Address</h3>
              <div className="space-y-2">
                <Input
                  id="dadd1"
                  name="dadd1"
                  value={formData.dadd1 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 1"
                  aria-label="Postal address line 1"
                  disabled={mutation.isPending}
                />
                <Input
                  id="dadd2"
                  name="dadd2"
                  value={formData.dadd2 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 2"
                  aria-label="Postal address line 2"
                  disabled={mutation.isPending}
                />
                <Input
                  id="dadd3"
                  name="dadd3"
                  value={formData.dadd3 || ''}
                  onChange={handleChange}
                  placeholder="City"
                  aria-label="Postal address city"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold mb-3 text-gray-700">Delivery Address</h3>
              <div className="space-y-2">
                <Input
                  id="delad1"
                  name="delad1"
                  value={formData.delad1 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 1"
                  aria-label="Delivery address line 1"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delad2"
                  name="delad2"
                  value={formData.delad2 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 2"
                  aria-label="Delivery address line 2"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delad3"
                  name="delad3"
                  value={formData.delad3 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 3"
                  aria-label="Delivery address line 3"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delad4"
                  name="delad4"
                  value={formData.delad4 || ''}
                  onChange={handleChange}
                  placeholder="City"
                  aria-label="Delivery address city"
                  disabled={mutation.isPending}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Pricing</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="price" className="block text-sm font-medium mb-1">
                  Price List
                </label>
                <select
                  id="price"
                  name="price"
                  value={formData.price || 1}
                  onChange={handleChange}
                  className="w-full border rounded-md px-3 py-2 h-10 text-sm"
                  disabled={mutation.isPending}
                >
                  <option value={1}>List 1</option>
                  <option value={2}>List 2</option>
                  <option value={3}>List 3</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="ddiscper" className="block text-sm font-medium mb-1">
                  Trade Discount (%)
                </label>
                <Input
                  id="ddiscper"
                  name="ddiscper"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.ddiscper || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>
              
              <div>
                <label htmlFor="pdisc" className="block text-sm font-medium mb-1">
                  Prompt Discount (%)
                </label>
                <Input
                  id="pdisc"
                  name="pdisc"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.pdisc || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div>
              <label htmlFor="terms" className="block text-sm font-medium mb-1">
                Payment Terms (days)
              </label>
              <Input
                id="terms"
                name="terms"
                type="number"
                min="0"
                value={formData.terms || 30}
                onChange={handleChange}
                placeholder="30"
                disabled={mutation.isPending}
              />
            </div>

            <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-800">
              <p>Trade discount is applied automatically to all invoices for this customer.</p>
              <p className="mt-1">Prompt discount is earned for payment within terms.</p>
            </div>
          </div>
        </section>

        {/* Credit Section */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Credit</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="dclimit" className="block text-sm font-medium mb-1">
                  Credit Limit
                </label>
                <Input
                  id="dclimit"
                  name="dclimit"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.dclimit || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>
              
              <div>
                <label htmlFor="darea" className="block text-sm font-medium mb-1">
                  Sales Area
                </label>
                <Input
                  id="darea"
                  name="darea"
                  type="number"
                  min="0"
                  value={formData.darea || 0}
                  onChange={handleChange}
                  placeholder="0"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="dintflag"
                name="dintflag"
                checked={(formData.dintflag === 'Y' || formData.dintflag === true) as boolean}
                onChange={handleChange}
                className="w-4 h-4 rounded border-gray-300"
                disabled={mutation.isPending}
              />
              <label htmlFor="dintflag" className="text-sm">
                Charge interest on overdue balances
              </label>
            </div>
          </div>
        </section>

        {/* Settings Section */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Settings</h2>
          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active !== false}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-gray-300"
                  disabled={mutation.isPending}
                />
                <label htmlFor="is_active" className="text-sm font-medium">
                  Account is active
                </label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="blockflag"
                  name="blockflag"
                  checked={(formData.blockflag === 'Y' || formData.blockflag === true) as boolean}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-gray-300"
                  disabled={mutation.isPending}
                  aria-describedby="blockflag-hint"
                />
                <label htmlFor="blockflag" className="text-sm font-medium text-red-600">
                  Block account (prevents new transactions)
                </label>
              </div>
              <p id="blockflag-hint" className="text-xs text-gray-500 ml-6">
                Blocked accounts cannot create new orders or invoices
              </p>
            </div>

            {isEdit && formData.id && (
              <Card className="p-4 bg-gray-50">
                <dl className="space-y-1 text-xs text-gray-600">
                  <div>
                    <dt className="font-semibold inline">Created: </dt>
                    <dd className="inline">
                      {formData.created_at 
                        ? new Date(formData.created_at).toLocaleString() 
                        : 'N/A'}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold inline">Last Updated: </dt>
                    <dd className="inline">
                      {formData.updated_at 
                        ? new Date(formData.updated_at).toLocaleString() 
                        : 'N/A'}
                    </dd>
                  </div>
                </dl>
              </Card>
            )}
          </div>
        </section>
      </div>

      {/* Submit Buttons */}
      <div className="flex gap-3 pt-6 border-t">
        <Button
          type="submit"
          disabled={mutation.isPending}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          aria-busy={mutation.isPending}
        >
          {mutation.isPending && <Loader className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />}
          {isEdit ? 'Update Account' : 'Create Account'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => window.history.back()}
          disabled={mutation.isPending}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}

// Helper Functions

/**
 * Validates form data before submission
 */
function validateForm(data: FormData): string | null {
  if (!data.dname?.trim()) {
    return 'Debtor name is required';
  }
  
  if (!data.dsname?.trim()) {
    return 'Short name is required';
  }
  
  if (data.dsname.length > MAX_SHORT_NAME_LENGTH) {
    return `Short name must be ${MAX_SHORT_NAME_LENGTH} characters or less`;
  }
  
  if ((data.ddiscper ?? 0) < 0 || (data.ddiscper ?? 0) > 100) {
    return 'Trade discount must be between 0 and 100';
  }
  
  if ((data.pdisc ?? 0) < 0 || (data.pdisc ?? 0) > 100) {
    return 'Prompt discount must be between 0 and 100';
  }
  
  if ((data.terms ?? 0) < 0) {
    return 'Payment terms cannot be negative';
  }
  
  if (data.dclimit !== undefined && data.dclimit < 0) {
    return 'Credit limit cannot be negative';
  }
  
  return null;
}

/**
 * Prepares form data for API submission
 * Converts boolean flags to API format if needed
 */
function prepareSubmitData(data: FormData, isEdit: boolean): DebtorCreateData | DebtorEditData {
  const submitData = { ...data };
  
  // Remove metadata fields that shouldn't be submitted
  if (isEdit) {
    delete (submitData as any).created_at;
    delete (submitData as any).updated_at;
    delete (submitData as any).id;
  }
  
  // If your API expects 'Y'/'N' instead of boolean, uncomment this:
  // submitData.dintflag = data.dintflag ? 'Y' : 'N';
  // submitData.blockflag = data.blockflag ? 'Y' : 'N';
  
  return submitData as DebtorCreateData | DebtorEditData;
}