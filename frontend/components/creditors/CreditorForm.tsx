'use client';

import { useState, useEffect } from 'react';
import { Supplier, SupplierCreateData, useCreditorsAPI, CreditTermsOption } from '@/lib/creditorsApi';

interface CreditorFormProps {
  creditor?: Supplier;
  onSuccess?: (creditor: Supplier) => void;
  onCancel?: () => void;
}

export default function CreditorForm({ creditor, onSuccess, onCancel }: CreditorFormProps) {
  const api = useCreditorsAPI();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [creditTermsOptions, setCreditTermsOptions] = useState<CreditTermsOption[]>([]);

  const [formData, setFormData] = useState<Record<string, any>>({
    supplier_number: '',
    account_number: '',
    name: '',
    short_name: '',
    physical_address_line1: '',
    physical_address_line2: '',
    physical_address_line3: '',
    physical_city: '',
    physical_postal_code: '',
    postal_address_line1: '',
    postal_address_line2: '',
    postal_address_line3: '',
    postal_city: '',
    postal_postal_code: '',
    telephone: '',
    telephone2: '',
    fax: '',
    email: '',
    contact_person: '',
    account_type: 'BBF',
    our_account_number: '',
    update_selling_price_on_receipt: false,
    credit_terms: null,
    prompt_payment_discount_percent: 0,
    bank_name: '',
    bank_branch_code: '',
    bank_account_number: '',
    vat_number: '',
    is_active: true,
  });

  // Load existing creditor data if editing
  useEffect(() => {
    if (creditor) {
      const c = creditor as any;
      setFormData({
        supplier_number: c.supplier_number || '',
        account_number: c.account_number || c.supplier_number || '',
        name: c.name || '',
        short_name: c.short_name || '',
        physical_address_line1: c.physical_address_line1 || '',
        physical_address_line2: c.physical_address_line2 || '',
        physical_address_line3: c.physical_address_line3 || '',
        physical_city: c.physical_city || '',
        physical_postal_code: c.physical_postal_code || '',
        postal_address_line1: c.postal_address_line1 || '',
        postal_address_line2: c.postal_address_line2 || '',
        postal_address_line3: c.postal_address_line3 || '',
        postal_city: c.postal_city || '',
        postal_postal_code: c.postal_postal_code || '',
        telephone: c.telephone || '',
        telephone2: c.telephone2 || '',
        fax: c.fax || '',
        email: c.email || '',
        contact_person: c.contact_person || '',
        account_type: c.account_type || 'BBF',
        our_account_number: c.our_account_number || '',
        update_selling_price_on_receipt: c.update_selling_price_on_receipt || false,
        credit_terms: c.credit_terms || null,
        prompt_payment_discount_percent: c.prompt_payment_discount_percent || 0,
        bank_name: c.bank_name || '',
        // ✅ Fixed: was c.branch_code and c.account_number (wrong keys)
        bank_branch_code: c.bank_branch_code || '',
        bank_account_number: c.bank_account_number || '',
        vat_number: c.vat_number || '',
        is_active: c.is_active !== false,
      });
    }
  }, [creditor]);

  // Load credit terms options
  useEffect(() => {
    const loadCreditTerms = async () => {
      try {
        const terms = await api.listCreditTerms();
        setCreditTermsOptions(terms);
      } catch (err) {
        console.error('Failed to load credit terms:', err);
      }
    };
    loadCreditTerms();
  }, [api]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    // Clear field error when user starts editing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }

    setFormData((prev: Record<string, any>) => {
      let newValue: any;

      if (type === 'checkbox') {
        newValue = checked;
      } else if (name === 'credit_terms') {
        newValue = value ? parseInt(value, 10) : null;
      } else if (name === 'supplier_number') {
        newValue = value;
        return {
          ...prev,
          [name]: newValue,
          account_number: newValue,
        };
      } else if (type === 'number') {
        newValue = parseFloat(value) || 0;
      } else {
        newValue = value;
      }

      return {
        ...prev,
        [name]: newValue,
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setLoading(true);

    try {
      // Client-side required field validation
      if (!formData.supplier_number?.toString().trim()) {
        setError('Supplier number is required');
        setLoading(false);
        return;
      }
      if (!formData.account_number?.toString().trim()) {
        setError('Account number is required');
        setLoading(false);
        return;
      }
      if (!formData.name?.trim()) {
        setError('Supplier name is required');
        setLoading(false);
        return;
      }

      // Strip empty strings and nulls (but keep credit_terms: null so it can be cleared)
      const submitData: any = {};
      Object.entries(formData).forEach(([key, value]) => {
        if (value === '' || (value === null && key !== 'credit_terms') || (value === 0 && key === 'credit_terms')) {
          return;
        }
        submitData[key] = value;
      });

      console.log('Submitting:', JSON.stringify(submitData, null, 2));

      if (creditor && creditor.supplier_number) {
        const updated = await api.updateSupplier(creditor.supplier_number, submitData);
        onSuccess?.(updated);
      } else {
        const created = await api.createSupplier(submitData);
        onSuccess?.(created);
      }
    } catch (err: any) {
      console.error('=== SUBMISSION ERROR ===', err);

      // Unwrap structured API error - handles fetch, axios, and custom api wrappers
      const apiError =
        err?.response?.data?.error ??  // axios
        err?.data?.error ??            // custom wrapper
        err?.error ??                  // direct throw of error object
        null;

      if (apiError?.field_errors) {
        // Map each field error into state so inputs can show inline messages
        const mapped: Record<string, string> = {};
        Object.entries(apiError.field_errors).forEach(([field, messages]) => {
          mapped[field] = (messages as string[])[0];
        });
        setFieldErrors(mapped);
        setError('Please correct the highlighted fields below.');
      } else {
        setError(apiError?.message ?? err?.message ?? 'An error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const isEditing = !!creditor;

  // ── Reusable field components ─────────────────────────────────────────────

  /** Standard text input with server-side error display and optional maxLength */
  const TextInput = ({
    name,
    label,
    type = 'text',
    required = false,
    disabled = false,
    placeholder = '',
    maxLength,
  }: {
    name: string;
    label: string;
    type?: string;
    required?: boolean;
    disabled?: boolean;
    placeholder?: string;
    maxLength?: number;
  }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        name={name}
        value={formData[name]}
        onChange={handleInputChange}
        disabled={disabled}
        placeholder={placeholder}
        maxLength={maxLength}
        className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 ${
          fieldErrors[name] ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'
        }`}
      />
      {maxLength && (
        <p className="mt-1 text-xs text-gray-400 text-right">
          {(formData[name] as string)?.length ?? 0}/{maxLength}
        </p>
      )}
      {fieldErrors[name] && (
        <p className="mt-1 text-xs text-red-600">{fieldErrors[name]}</p>
      )}
    </div>
  );

  /** Address input — always max 20 chars per Django model constraint */
  const AddressInput = ({ name, label }: { name: string; label: string }) => (
    <TextInput name={name} label={label} maxLength={20} />
  );

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">

      {/* Global error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* ── Basic Information ──────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Supplier Number <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="supplier_number"
              value={formData.supplier_number}
              onChange={handleInputChange}
              disabled={isEditing}
              placeholder={isEditing ? '' : 'Enter supplier number'}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 ${
                fieldErrors.supplier_number ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {fieldErrors.supplier_number && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.supplier_number}</p>
            )}
            <input type="hidden" name="account_number" value={formData.account_number} />
          </div>

          <TextInput name="name" label="Supplier Name" required />
          <TextInput name="short_name" label="Short Name" />
        </div>
      </section>

      {/* ── Contact Information ────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Contact Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput name="email" label="Email" type="email" />
          <TextInput name="contact_person" label="Contact Person" />
          <TextInput name="telephone" label="Telephone 1" type="tel" />
          <TextInput name="telephone2" label="Telephone 2" type="tel" />
          <TextInput name="fax" label="Fax" type="tel" />
        </div>
      </section>

      {/* ── Physical Address ───────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Physical Address</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AddressInput name="physical_address_line1" label="Address Line 1" />
          <AddressInput name="physical_address_line2" label="Address Line 2" />
          <AddressInput name="physical_address_line3" label="Address Line 3" />
          <AddressInput name="physical_city" label="City" />
          <AddressInput name="physical_postal_code" label="Postal Code" />
        </div>
      </section>

      {/* ── Postal Address ─────────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Postal Address</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AddressInput name="postal_address_line1" label="Address Line 1" />
          <AddressInput name="postal_address_line2" label="Address Line 2" />
          <AddressInput name="postal_address_line3" label="Address Line 3" />
          <AddressInput name="postal_city" label="City" />
          <AddressInput name="postal_postal_code" label="Postal Code" />
        </div>
      </section>

      {/* ── Account Settings ───────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Account Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Account Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Account Type</label>
            <select
              name="account_type"
              value={formData.account_type}
              onChange={handleInputChange}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.account_type ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">-- Select Account Type --</option>
              <option value="BBF">Balance Brought Forward</option>
              <option value="OI">Open Item</option>
            </select>
            {fieldErrors.account_type && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.account_type}</p>
            )}
          </div>

          <TextInput name="our_account_number" label="Our Account Number" />

          {/* Credit Terms — shows spinner while loading, error if none available */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Credit Terms</label>
            <select
              name="credit_terms"
              value={formData.credit_terms ? String(formData.credit_terms) : ''}
              onChange={handleInputChange}
              disabled={creditTermsOptions.length === 0 && loading}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 ${
                fieldErrors.credit_terms ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              {creditTermsOptions.length === 0 ? (
                <option value="">-- No credit terms available --</option>
              ) : (
                <>
                  <option value="">-- Select Credit Terms --</option>
                  {creditTermsOptions.map(term => (
                    <option key={term.id} value={String(term.id)}>
                      {term.name}
                    </option>
                  ))}
                </>
              )}
            </select>
            {fieldErrors.credit_terms && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.credit_terms}</p>
            )}
            {creditTermsOptions.length === 0 && (
              <p className="mt-1 text-xs text-amber-600">
                ⚠ Credit terms could not be loaded. Check your connection or add terms in settings.
              </p>
            )}
          </div>

          {/* Prompt Payment Discount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt Payment Discount (%)
            </label>
            <input
              type="number"
              name="prompt_payment_discount_percent"
              value={formData.prompt_payment_discount_percent}
              onChange={handleInputChange}
              min="0"
              max="100"
              step="0.01"
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                fieldErrors.prompt_payment_discount_percent ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {fieldErrors.prompt_payment_discount_percent && (
              <p className="mt-1 text-xs text-red-600">{fieldErrors.prompt_payment_discount_percent}</p>
            )}
          </div>

          {/* Checkboxes */}
          <div className="flex items-center gap-2 mt-6">
            <input
              type="checkbox"
              name="update_selling_price_on_receipt"
              checked={formData.update_selling_price_on_receipt}
              onChange={handleInputChange}
              className="w-4 h-4 rounded border-gray-300"
            />
            <label className="text-sm font-medium text-gray-700">
              Update selling price on receipt
            </label>
          </div>

          <div className="flex items-center gap-2 mt-6">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleInputChange}
              className="w-4 h-4 rounded border-gray-300"
            />
            <label className="text-sm font-medium text-gray-700">Active</label>
          </div>
        </div>
      </section>

      {/* ── Banking Details ────────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Banking Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TextInput name="bank_name" label="Bank Name" />
          <TextInput name="bank_branch_code" label="Branch Code" />
          <TextInput name="bank_account_number" label="Account Number" />
        </div>
      </section>

      {/* ── Tax Information ────────────────────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Tax Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput name="vat_number" label="VAT Number" />
        </div>
      </section>

      {/* ── Form Actions ───────────────────────────────────────────────────── */}
      <div className="flex gap-3 pt-6 border-t border-gray-200">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 font-medium"
        >
          {loading ? 'Saving...' : isEditing ? 'Update' : 'Create'} Creditor
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 disabled:bg-gray-400 font-medium"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}