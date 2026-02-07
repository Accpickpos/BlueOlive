'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';
import ConvertCategoryModal from './ConvertCategoryModal';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
}

interface DebtorFormData {
  account_number: string;
  name: string;
  search_name: string;
  contact_person: string;
  telephone1: string;
  telephone2: string;
  fax: string;
  email: string;
  additional_info: string;
  postal_address_line1: string;
  postal_address_line2: string;
  postal_address_line3: string;
  postal_code: string;
  delivery_address_line1: string;
  delivery_address_line2: string;
  delivery_address_line3: string;
  delivery_code: string;
  vat_number: string;
  assigned_user: number | null;
  account_category: string;
  trade_discount: number;
  credit_limit: number;
  price_level: number;
  terms: number;
  prompt_discount_percentage: number;
  print_discount_on_invoice: boolean;
  charge_interest: boolean;
  print_balance_on_documents: boolean;
  is_blocked: boolean;
  block_reason: string;
  block_invoicing: boolean;
  block_receipts: boolean;
  is_active: boolean;
}

const initialFormData: DebtorFormData = {
  account_number: '',
  name: '',
  search_name: '',
  contact_person: '',
  telephone1: '',
  telephone2: '',
  fax: '',
  email: '',
  additional_info: '',
  postal_address_line1: '',
  postal_address_line2: '',
  postal_address_line3: '',
  postal_code: '',
  delivery_address_line1: '',
  delivery_address_line2: '',
  delivery_address_line3: '',
  delivery_code: '',
  vat_number: '',
  assigned_user: null,
  account_category: '',
  trade_discount: 0,
  credit_limit: 0,
  price_level: 1,
  terms: 30,
  prompt_discount_percentage: 0,
  print_discount_on_invoice: false,
  charge_interest: false,
  print_balance_on_documents: true,
  is_blocked: false,
  block_reason: '',
  block_invoicing: false,
  block_receipts: false,
  is_active: true,
};

interface DebtorFormProps {
  debtorId?: number;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function DebtorForm({ debtorId, onSuccess, onCancel }: DebtorFormProps) {
  const [formData, setFormData] = useState<DebtorFormData>(initialFormData);
  const [salesAreas, setSalesAreas] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [conversionResult, setConversionResult] = useState<any>(null);

  // Fetch debtor data if editing
  useEffect(() => {
    if (debtorId) {
      fetchDebtorData();
    }
    fetchUsers();
  }, [debtorId]);

  const fetchDebtorData = async () => {
    try {
      setLoading(true);
      const response = await apiRequest(`/api/debtors/${debtorId}/`);
      // Normalize null values to empty strings for controlled inputs
      const normalizedData = {
        ...response.data,
        contact_person: response.data.contact_person || '',
        telephone1: response.data.telephone1 || '',
        telephone2: response.data.telephone2 || '',
        fax: response.data.fax || '',
        email: response.data.email || '',
        additional_info: response.data.additional_info || '',
        postal_address_line1: response.data.postal_address_line1 || '',
        postal_address_line2: response.data.postal_address_line2 || '',
        postal_address_line3: response.data.postal_address_line3 || '',
        postal_code: response.data.postal_code || '',
        delivery_address_line1: response.data.delivery_address_line1 || '',
        delivery_address_line2: response.data.delivery_address_line2 || '',
        delivery_address_line3: response.data.delivery_address_line3 || '',
        delivery_code: response.data.delivery_code || '',
        vat_number: response.data.vat_number || '',
        block_reason: response.data.block_reason || '',
      };
      setFormData(normalizedData);
      setError(null);
    } catch (err) {
      setError('Failed to load debtor data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await apiRequest(`/api/users/`);
      setSalesAreas(response.data.results || response.data);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, type, value } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData((prev) => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked : name === 'assigned_user' ? (value ? parseInt(value) : null) : value,
      };
      
      // Auto-populate search_name from name (uppercase)
      if (name === 'name' && value) {
        updated.search_name = value.toUpperCase();
      }
      
      return updated;
    });
  };

  const handleConversionSuccess = async (result: any) => {
    setConversionResult(result);
    setShowConvertModal(false);
    // Reload the form to show updated category
    if (debtorId) {
      await fetchDebtorData();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const endpoint = debtorId
        ? `/api/debtors/${debtorId}/`
        : `/api/debtors/`;

      const method = debtorId ? 'PATCH' : 'POST';

      console.log('DebtorForm submit:', { 
        endpoint, 
        method, 
        formData: {
          account_number: formData.account_number,
          name: formData.name,
          search_name: formData.search_name,
          assigned_user: formData.assigned_user,
          // Show a few key fields
          email: formData.email,
          is_active: formData.is_active,
          account_category: formData.account_category,
        }
      });
      console.log('DebtorForm submit data:', JSON.stringify({ 
        account_number: formData.account_number,
        name: formData.name,
        search_name: formData.search_name,
        assigned_user: formData.assigned_user,
        email: formData.email,
        is_active: formData.is_active,
        account_category: formData.account_category,
      }, null, 2));
      
      const response = await apiRequest(endpoint, {
        method,
        body: formData,
      });

      console.log('DebtorForm submit success:', { status: response.status, data: response.data });

      setSuccess(true);
      if (!debtorId) {
        setFormData(initialFormData);
      }
      if (onSuccess) {
        setTimeout(onSuccess, 1000);
      }
    } catch (err: any) {
      const errorStatus = err.response?.status;
      const errorData = err.response?.data;
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || err.message || 'Failed to save debtor';
      
      setError(errorMessage);
      
      // Log complete error information for debugging
      const logData: any = {
        status: errorStatus,
        data: errorData,
        message: errorMessage,
        errorType: err.code,
        errorName: err.name,
        isNetworkError: !err.response,
      };
      
      // If it's a 400 with field errors, log them specially
      if (errorStatus === 400 && typeof errorData === 'object') {
        logData.fieldErrors = errorData;
        logData.fieldsWithErrors = Object.keys(errorData).filter(key => errorData[key]);
      }
      
      console.error('Submit error:', logData);
      console.error('Submit error details:', JSON.stringify(logData, null, 2));
    } finally {
      setLoading(false);
    }
  };

  if (loading && debtorId) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-6xl mx-auto">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          Debtor saved successfully!
        </div>
      )}

      {/* Basic Information */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Number *
            </label>
            <input
              type="text"
              name="account_number"
              value={formData.account_number}
              onChange={handleChange}
              disabled={!!debtorId}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Person
            </label>
            <input
              type="text"
              name="contact_person"
              value={formData.contact_person}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telephone 1
            </label>
            <input
              type="text"
              name="telephone1"
              value={formData.telephone1}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telephone 2
            </label>
            <input
              type="text"
              name="telephone2"
              value={formData.telephone2}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fax
            </label>
            <input
              type="text"
              name="fax"
              value={formData.fax}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              VAT Number
            </label>
            <input
              type="text"
              name="vat_number"
              value={formData.vat_number}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assigned User (Salesperson)
            </label>
            <select
              name="assigned_user"
              value={formData.assigned_user || ''}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            >
              <option value="">Select User</option>
              {salesAreas.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.username} ({user.email})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Postal Address */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Postal Address</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 1
            </label>
            <input
              type="text"
              name="postal_address_line1"
              value={formData.postal_address_line1}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 2
            </label>
            <input
              type="text"
              name="postal_address_line2"
              value={formData.postal_address_line2}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 3
            </label>
            <input
              type="text"
              name="postal_address_line3"
              value={formData.postal_address_line3}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Postal Code
            </label>
            <input
              type="text"
              name="postal_code"
              value={formData.postal_code}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Delivery Address */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Delivery Address</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 1
            </label>
            <input
              type="text"
              name="delivery_address_line1"
              value={formData.delivery_address_line1}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 2
            </label>
            <input
              type="text"
              name="delivery_address_line2"
              value={formData.delivery_address_line2}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Line 3
            </label>
            <input
              type="text"
              name="delivery_address_line3"
              value={formData.delivery_address_line3}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Delivery Code
            </label>
            <input
              type="text"
              name="delivery_code"
              value={formData.delivery_code}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Account Settings */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Account Settings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Category
            </label>
            <div className="flex gap-2">
              <select
                name="account_category"
                value={formData.account_category}
                onChange={handleChange}
                disabled={debtorId !== undefined}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">Balance Brought Forward</option>
                <option value="O">Open Item</option>
                <option value="C">Cash Customer</option>
              </select>
              {debtorId && (
                <button
                  type="button"
                  onClick={() => setShowConvertModal(true)}
                  className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 whitespace-nowrap text-sm font-medium"
                  title="Convert to different account category"
                >
                  Convert
                </button>
              )}
            </div>
            {debtorId && (
              <p className="text-xs text-gray-500 mt-1">
                Use the Convert button to change the account category with safe data migration
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Credit Limit
            </label>
            <input
              type="number"
              name="credit_limit"
              value={formData.credit_limit}
              onChange={handleChange}
              min="0"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trade Discount (%)
            </label>
            <input
              type="number"
              name="trade_discount"
              value={formData.trade_discount}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price Level
            </label>
            <select
              name="price_level"
              value={formData.price_level}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            >
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Terms (Days)
            </label>
            <input
              type="number"
              name="terms"
              value={formData.terms}
              onChange={handleChange}
              min="0"
              step="1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prompt Discount (%)
            </label>
            <input
              type="number"
              name="prompt_discount_percentage"
              value={formData.prompt_discount_percentage}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Checkboxes */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Options</h2>
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              name="print_discount_on_invoice"
              checked={formData.print_discount_on_invoice}
              onChange={handleChange}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200"
            />
            <span className="ml-2 text-sm text-gray-700">Print Discount on Invoice</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="charge_interest"
              checked={formData.charge_interest}
              onChange={handleChange}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200"
            />
            <span className="ml-2 text-sm text-gray-700">Charge Interest</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="print_balance_on_documents"
              checked={formData.print_balance_on_documents}
              onChange={handleChange}
              className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200"
            />
            <span className="ml-2 text-sm text-gray-700">Print Balance on Documents</span>
          </label>
        </div>
      </div>

      {/* Block Status */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Block Status</h2>
        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              name="is_blocked"
              checked={formData.is_blocked}
              onChange={handleChange}
              className="rounded border-gray-300 text-red-600 shadow-sm focus:border-red-300 focus:ring focus:ring-red-200"
            />
            <span className="ml-2 text-sm text-gray-700">Block Debtor</span>
          </label>
          {formData.is_blocked && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Block Reason
              </label>
              <textarea
                name="block_reason"
                value={formData.block_reason}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>
          )}
          <label className="flex items-center">
            <input
              type="checkbox"
              name="block_invoicing"
              checked={formData.block_invoicing}
              onChange={handleChange}
              className="rounded border-gray-300 text-red-600 shadow-sm focus:border-red-300 focus:ring focus:ring-red-200"
            />
            <span className="ml-2 text-sm text-gray-700">Block Invoicing</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="block_receipts"
              checked={formData.block_receipts}
              onChange={handleChange}
              className="rounded border-gray-300 text-red-600 shadow-sm focus:border-red-300 focus:ring focus:ring-red-200"
            />
            <span className="ml-2 text-sm text-gray-700">Block Receipts</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="rounded border-gray-300 text-green-600 shadow-sm focus:border-green-300 focus:ring focus:ring-green-200"
            />
            <span className="ml-2 text-sm text-gray-700">Active</span>
          </label>
        </div>
      </div>

      {/* Additional Info */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Additional Information</h2>
        <textarea
          name="additional_info"
          value={formData.additional_info}
          onChange={handleChange}
          rows={4}
          placeholder="Additional notes about this debtor..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
        />
      </div>

      {/* Conversion Result Alert */}
      {conversionResult && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
          <p className="font-medium">✓ Account Category Converted</p>
          <p className="text-sm mt-1">{conversionResult.message}</p>
          {conversionResult.transactions_created > 0 && (
            <p className="text-sm mt-1">
              Created {conversionResult.transactions_created} transaction records
            </p>
          )}
          {conversionResult.transactions_aggregated > 0 && (
            <p className="text-sm mt-1">
              Aggregated {conversionResult.transactions_aggregated} transactions into aging buckets
            </p>
          )}
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-4 justify-end">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : debtorId ? 'Update Debtor' : 'Create Debtor'}
        </button>
      </div>

      {/* Convert Category Modal */}
      {debtorId && (
        <ConvertCategoryModal
          isOpen={showConvertModal}
          debtorId={debtorId}
          debtorName={formData.name}
          currentCategory={formData.account_category}
          onSuccess={handleConversionSuccess}
          onCancel={() => setShowConvertModal(false)}
        />
      )}
    </form>
  );
}
