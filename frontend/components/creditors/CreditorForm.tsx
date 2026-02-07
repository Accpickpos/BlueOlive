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
  const [creditTermsOptions, setCreditTermsOptions] = useState<CreditTermsOption[]>([]);
  
  const [formData, setFormData] = useState<SupplierCreateData>({
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
    telephone1: '',
    telephone2: '',
    fax: '',
    email: '',
    contact_person: '',
    account_type: 'BBF', // Default account type (Balance Brought Forward)
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
      setFormData({
        supplier_number: creditor.supplier_number || '',
        account_number: creditor.account_number || creditor.supplier_number || '',
        name: creditor.name || '',
        short_name: creditor.short_name || '',
        physical_address_line1: creditor.physical_address_line1 || '',
        physical_address_line2: creditor.physical_address_line2 || '',
        physical_address_line3: creditor.physical_address_line3 || '',
        physical_city: creditor.physical_city || '',
        physical_postal_code: creditor.physical_postal_code || '',
        postal_address_line1: creditor.postal_address_line1 || '',
        postal_address_line2: creditor.postal_address_line2 || '',
        postal_address_line3: creditor.postal_address_line3 || '',
        postal_city: creditor.postal_city || '',
        postal_postal_code: creditor.postal_postal_code || '',
        telephone1: creditor.telephone1 || '',
        telephone2: creditor.telephone2 || '',
        fax: creditor.fax || '',
        email: creditor.email || '',
        contact_person: creditor.contact_person || '',
        account_type: creditor.account_type || 'BBF',
        our_account_number: creditor.our_account_number || '',
        update_selling_price_on_receipt: creditor.update_selling_price_on_receipt || false,
        credit_terms: creditor.credit_terms || undefined,
        prompt_payment_discount_percent: creditor.prompt_payment_discount_percent || 0,
        bank_name: creditor.bank_name || '',
        bank_branch_code: creditor.bank_branch_code || '',
        bank_account_number: creditor.bank_account_number || '',
        vat_number: creditor.vat_number || '',
        is_active: creditor.is_active !== false,
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
    
    setFormData(prev => {
      let newValue: any;
      
      if (type === 'checkbox') {
        newValue = checked;
      } else if (name === 'credit_terms') {
        // Special handling for credit_terms - only set if value is not empty
        newValue = value ? parseInt(value, 10) : null;
        console.log(`Credit Terms changed: "${value}" -> ${newValue}`);
      } else if (name === 'supplier_number') {
        // Keep as string for supplier number, and sync with account_number
        newValue = value;
        console.log(`Supplier Number changed: "${value}"`);
        // Also update account_number to match supplier_number
        return {
          ...prev,
          [name]: newValue,
          account_number: newValue  // Keep in sync
        };
      } else if (name === 'account_number') {
        // Also allow direct editing of account_number
        newValue = value;
        console.log(`Account Number changed: "${value}"`);
        return {
          ...prev,
          [name]: newValue
        };
      } else if (type === 'number') {
        newValue = parseFloat(value) || 0;
      } else {
        newValue = value;
      }
      
      console.log(`Field ${name} changed to:`, newValue);
      
      return {
        ...prev,
        [name]: newValue
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate supplier_number and account_number
      if (!formData.supplier_number || formData.supplier_number.toString().trim() === '') {
        setError('Supplier number is required');
        setLoading(false);
        return;
      }
      if (!formData.account_number || formData.account_number.toString().trim() === '') {
        setError('Account number is required');
        setLoading(false);
        return;
      }

      // Validate required name
      if (!formData.name || formData.name.trim() === '') {
        setError('Supplier name is required');
        setLoading(false);
        return;
      }

      // Log the form data before submission
      console.log('=== CREDITOR FORM SUBMISSION ===');
      console.log('Supplier Number:', formData.supplier_number);
      console.log('Account Number:', formData.account_number);
      console.log('Name:', formData.name);
      console.log('Account Type:', formData.account_type);
      console.log('Credit Terms:', formData.credit_terms, 'Type:', typeof formData.credit_terms);
      console.log('Full Form Data:', JSON.stringify(formData, null, 2));
      
      // Prepare data - remove empty/null fields
      const submitData: any = { ...formData };
      
      // Remove fields with empty strings or null values (except account_type which needs a valid value)
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === '' || 
            (submitData[key] === null && key !== 'credit_terms') ||
            (submitData[key] === 0 && key === 'credit_terms')) {
          delete submitData[key];
          console.log(`Removed ${key} from submission (empty/null)`);
        }
      });
      
      console.log('Data to submit:', JSON.stringify(submitData, null, 2));
      
      if (creditor && creditor.supplier_number) {
        // Update existing
        console.log('Updating supplier with number:', creditor.supplier_number);
        const updated = await api.updateSupplier(creditor.supplier_number, submitData);
        console.log('Update successful:', updated);
        onSuccess?.(updated);
      } else {
        // Create new
        console.log('Creating new supplier');
        const created = await api.createSupplier(submitData);
        console.log('Creation successful:', created);
        onSuccess?.(created);
      }
    } catch (err) {
      console.error('=== SUBMISSION ERROR ===');
      console.error('Error details:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const isEditing = !!creditor;

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Basic Information */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Supplier Number *
            </label>
            <input
              type="number"
              name="supplier_number"
              value={formData.supplier_number}
              onChange={handleInputChange}
              disabled={isEditing}
              placeholder={isEditing ? '' : 'Enter supplier number'}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            />
            {/* Hidden field for account_number - synced with supplier_number */}
            <input
              type="hidden"
              name="account_number"
              value={formData.account_number}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Supplier Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Short Name
            </label>
            <input
              type="text"
              name="short_name"
              value={formData.short_name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Contact Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contact Person
            </label>
            <input
              type="text"
              name="contact_person"
              value={formData.contact_person}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Telephone 1
            </label>
            <input
              type="tel"
              name="telephone1"
              value={formData.telephone1}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Telephone 2
            </label>
            <input
              type="tel"
              name="telephone2"
              value={formData.telephone2}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fax
            </label>
            <input
              type="tel"
              name="fax"
              value={formData.fax}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Physical Address */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Physical Address</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 1
            </label>
            <input
              type="text"
              name="physical_address_line1"
              value={formData.physical_address_line1}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 2
            </label>
            <input
              type="text"
              name="physical_address_line2"
              value={formData.physical_address_line2}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 3
            </label>
            <input
              type="text"
              name="physical_address_line3"
              value={formData.physical_address_line3}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City
            </label>
            <input
              type="text"
              name="physical_city"
              value={formData.physical_city}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Postal Code
            </label>
            <input
              type="text"
              name="physical_postal_code"
              value={formData.physical_postal_code}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Postal Address */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Postal Address</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 1
            </label>
            <input
              type="text"
              name="postal_address_line1"
              value={formData.postal_address_line1}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 2
            </label>
            <input
              type="text"
              name="postal_address_line2"
              value={formData.postal_address_line2}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address Line 3
            </label>
            <input
              type="text"
              name="postal_address_line3"
              value={formData.postal_address_line3}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City
            </label>
            <input
              type="text"
              name="postal_city"
              value={formData.postal_city}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Postal Code
            </label>
            <input
              type="text"
              name="postal_postal_code"
              value={formData.postal_postal_code}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Account Settings */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Account Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Account Type
            </label>
            <select
              name="account_type"
              value={formData.account_type}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select Account Type --</option>
              <option value="BBF">Balance Brought Forward</option>
              <option value="OI">Open Item</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Our Account Number
            </label>
            <input
              type="text"
              name="our_account_number"
              value={formData.our_account_number}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Credit Terms
            </label>
            <select
              name="credit_terms"
              value={formData.credit_terms ? String(formData.credit_terms) : ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select Credit Terms --</option>
              {creditTermsOptions.map(term => (
                <option key={term.id} value={String(term.id)}>{term.name}</option>
              ))}
            </select>
          </div>

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
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

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
            <label className="text-sm font-medium text-gray-700">
              Active
            </label>
          </div>
        </div>
      </div>

      {/* Banking Details */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Banking Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bank Name
            </label>
            <input
              type="text"
              name="bank_name"
              value={formData.bank_name}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Branch Code
            </label>
            <input
              type="text"
              name="bank_branch_code"
              value={formData.bank_branch_code}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Account Number
            </label>
            <input
              type="text"
              name="bank_account_number"
              value={formData.bank_account_number}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* VAT */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Tax Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              VAT Number
            </label>
            <input
              type="text"
              name="vat_number"
              value={formData.vat_number}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Form Actions */}
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
