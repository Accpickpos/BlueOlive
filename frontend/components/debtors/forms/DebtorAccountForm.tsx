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
  customer_number: 0,
  name: '',
  short_name: '',
  contact_person: '',
  phone: '',
  fax: '',
  address_line1: '',
  address_line2: '',
  address_line3: '',
  postal_code: '',
  delivery_address1: '',
  delivery_address2: '',
  delivery_address3: '',
  delivery_address4: '',
  tax_number: '',
  account_type: '',
  price_level: 1,
  payment_terms: 30,
  discount_percentage: 0,
  prompt_payment_discount: 0,
  credit_limit: 0,
  area_code: 0,
  interest_flag: false,
  block_flag: false,
  is_active: true,
  discount_printable: false,
  positive_balance_only: false,
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
        interest_flag: initialData.interest_flag === 'Y' || initialData.interest_flag === true,
        block_flag: initialData.block_flag === 'Y' || initialData.block_flag === true,
        discount_printable: initialData.discount_printable === 'Y' || initialData.discount_printable === true,
        positive_balance_only: initialData.positive_balance_only === 'Y' || initialData.positive_balance_only === true,
      });
    }
  }, [initialData]);

  const mutation = useMutation({
    mutationFn: async () => {
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
                <label htmlFor="customer_number" className="block text-sm font-medium mb-1">
                  Account Number
                </label>
                <Input
                  id="customer_number"
                  name="customer_number"
                  value={formData.customer_number || ''}
                  onChange={handleChange}
                  placeholder="Auto-generated"
                  disabled={isEdit}
                  aria-describedby="customer_number-hint"
                />
                <p id="customer_number-hint" className="text-xs text-gray-500 mt-1">
                  {isEdit ? 'Cannot be changed' : 'Will be assigned automatically'}
                </p>
              </div>

              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  <span className="text-red-600">* </span>Debtor Name
                </label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name || ''}
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
                <label htmlFor="short_name" className="block text-sm font-medium mb-1">
                  <span className="text-red-600">* </span>Short Name
                </label>
                <Input
                  id="short_name"
                  name="short_name"
                  value={formData.short_name || ''}
                  onChange={handleChange}
                  placeholder="Max 20 characters"
                  maxLength={MAX_SHORT_NAME_LENGTH}
                  required
                  aria-required="true"
                  disabled={mutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="account_type" className="block text-sm font-medium mb-1">
                  Account Type
                </label>
                <select
                  id="account_type"
                  name="account_type"
                  value={formData.account_type || ''}
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
              <label htmlFor="contact_person" className="block text-sm font-medium mb-1">
                Contact Person
              </label>
              <Input
                id="contact_person"
                name="contact_person"
                value={formData.contact_person || ''}
                onChange={handleChange}
                placeholder="e.g., John Smith"
                maxLength={MAX_CONTACT_LENGTH}
                aria-describedby="contact_person-hint"
                disabled={mutation.isPending}
              />
              <p id="contact_person-hint" className="text-xs text-gray-500 mt-1">
                The person to ask for when calling about orders or payments
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium mb-1">
                  Telephone
                </label>
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone || ''}
                  onChange={handleChange}
                  placeholder="Primary phone"
                  disabled={mutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="fax" className="block text-sm font-medium mb-1">
                  Fax
                </label>
                <Input
                  id="fax"
                  name="fax"
                  type="tel"
                  value={formData.fax || ''}
                  onChange={handleChange}
                  placeholder="Fax number"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="tax_number" className="block text-sm font-medium mb-1">
                  Tax/VAT Number
                </label>
                <Input
                  id="tax_number"
                  name="tax_number"
                  value={formData.tax_number || ''}
                  onChange={handleChange}
                  placeholder="VAT registration"
                  disabled={mutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="postal_code" className="block text-sm font-medium mb-1">
                  Postal Code
                </label>
                <Input
                  id="postal_code"
                  name="postal_code"
                  value={formData.postal_code || ''}
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
                  id="address_line1"
                  name="address_line1"
                  value={formData.address_line1 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 1"
                  aria-label="Postal address line 1"
                  disabled={mutation.isPending}
                />
                <Input
                  id="address_line2"
                  name="address_line2"
                  value={formData.address_line2 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 2"
                  aria-label="Postal address line 2"
                  disabled={mutation.isPending}
                />
                <Input
                  id="address_line3"
                  name="address_line3"
                  value={formData.address_line3 || ''}
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
                  id="delivery_address1"
                  name="delivery_address1"
                  value={formData.delivery_address1 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 1"
                  aria-label="Delivery address line 1"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delivery_address2"
                  name="delivery_address2"
                  value={formData.delivery_address2 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 2"
                  aria-label="Delivery address line 2"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delivery_address3"
                  name="delivery_address3"
                  value={formData.delivery_address3 || ''}
                  onChange={handleChange}
                  placeholder="Address Line 3"
                  aria-label="Delivery address line 3"
                  disabled={mutation.isPending}
                />
                <Input
                  id="delivery_address4"
                  name="delivery_address4"
                  value={formData.delivery_address4 || ''}
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
                <label htmlFor="price_level" className="block text-sm font-medium mb-1">
                  Price List
                </label>
                <select
                  id="price_level"
                  name="price_level"
                  value={formData.price_level || 1}
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
                <label htmlFor="discount_percentage" className="block text-sm font-medium mb-1">
                  Trade Discount (%)
                </label>
                <Input
                  id="discount_percentage"
                  name="discount_percentage"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.discount_percentage || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="prompt_payment_discount" className="block text-sm font-medium mb-1">
                  Prompt Discount (%)
                </label>
                <Input
                  id="prompt_payment_discount"
                  name="prompt_payment_discount"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.prompt_payment_discount || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div>
              <label htmlFor="payment_terms" className="block text-sm font-medium mb-1">
                Payment Terms (days)
              </label>
              <Input
                id="payment_terms"
                name="payment_terms"
                type="number"
                min="0"
                value={formData.payment_terms || 30}
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
                <label htmlFor="credit_limit" className="block text-sm font-medium mb-1">
                  Credit Limit
                </label>
                <Input
                  id="credit_limit"
                  name="credit_limit"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.credit_limit || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                  disabled={mutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="area_code" className="block text-sm font-medium mb-1">
                  Sales Area
                </label>
                <Input
                  id="area_code"
                  name="area_code"
                  type="number"
                  min="0"
                  value={formData.area_code || 0}
                  onChange={handleChange}
                  placeholder="0"
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="interest_flag"
                name="interest_flag"
                checked={(formData.interest_flag === 'Y' || formData.interest_flag === true) as boolean}
                onChange={handleChange}
                className="w-4 h-4 rounded border-gray-300"
                disabled={mutation.isPending}
              />
              <label htmlFor="interest_flag" className="text-sm">
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
                  id="block_flag"
                  name="block_flag"
                  checked={(formData.block_flag === 'Y' || formData.block_flag === true) as boolean}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-gray-300"
                  disabled={mutation.isPending}
                  aria-describedby="block_flag-hint"
                />
                <label htmlFor="block_flag" className="text-sm font-medium text-red-600">
                  Block account (prevents new transactions)
                </label>
              </div>
              <p id="block_flag-hint" className="text-xs text-gray-500 ml-6">
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

function validateForm(data: FormData): string | null {
  if (!data.name?.trim()) {
    return 'Debtor name is required';
  }

  if (!data.short_name?.trim()) {
    return 'Short name is required';
  }

  if (data.short_name.length > MAX_SHORT_NAME_LENGTH) {
    return `Short name must be ${MAX_SHORT_NAME_LENGTH} characters or less`;
  }

  if ((data.discount_percentage ?? 0) < 0 || (data.discount_percentage ?? 0) > 100) {
    return 'Trade discount must be between 0 and 100';
  }

  if ((data.prompt_payment_discount ?? 0) < 0 || (data.prompt_payment_discount ?? 0) > 100) {
    return 'Prompt discount must be between 0 and 100';
  }

  if ((data.payment_terms ?? 0) < 0) {
    return 'Payment terms cannot be negative';
  }

  if (data.credit_limit !== undefined && data.credit_limit < 0) {
    return 'Credit limit cannot be negative';
  }

  return null;
}

function prepareSubmitData(data: FormData, isEdit: boolean): DebtorCreateData | DebtorEditData {
  const submitData = { ...data };

  if (isEdit) {
    delete (submitData as any).created_at;
    delete (submitData as any).updated_at;
    delete (submitData as any).id;
  }

  return submitData as DebtorCreateData | DebtorEditData;
}