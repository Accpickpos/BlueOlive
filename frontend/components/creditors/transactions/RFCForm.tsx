'use client';

import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import { useCreditorsAPI } from '@/lib/creditorsApi';

interface RFCFormProps {
  onComplete: () => void;
}

export default function RFCForm({ onComplete }: RFCFormProps) {
  const { listSuppliers } = useCreditorsAPI();
  
  const [formData, setFormData] = useState({
    supplier: '',
    rfc_type: 'SEND',
    return_date: new Date().toISOString().split('T')[0],
    stock_item: '',
    quantity: 0,
    reason: '',
    additional_reference: '',
  });

  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const rfcTypes = [
    { value: 'SEND', label: '1. Send Stock to Suppliers' },
    { value: 'CREDIT_GRANTED', label: '2. Update Supplier Returns - Credit Granted' },
    { value: 'STOCK_REPLACED', label: '2. Update Supplier Returns - Stock Replaced' },
    { value: 'VIEW_ITEM', label: '3. View RFC Status - By Stock Item' },
    { value: 'VIEW_SUPPLIER', label: '3. View RFC Status - By Supplier' },
    { value: 'VALUE', label: '4. Value of Stock RFC' },
  ];

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const suppliers = await listSuppliers();
      setSuppliers(suppliers);
    } catch (err) {
      console.error('Error fetching suppliers:', err);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'number' ? parseFloat(value) : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.supplier) {
        throw new Error('Please select a supplier');
      }

      if (!formData.stock_item) {
        throw new Error('Please enter a stock item');
      }

      if (formData.quantity <= 0) {
        throw new Error('Please enter a valid quantity');
      }

      // Note: In production, this would send to an RFC endpoint
      const payload = {
        supplier: formData.supplier,
        rfc_type: formData.rfc_type,
        return_date: formData.return_date,
        stock_item: formData.stock_item,
        quantity: parseFloat(formData.quantity.toString()),
        reason: formData.reason,
        additional_reference: formData.additional_reference,
      };

      // For now, just simulate success
      setSuccess('RFC transaction recorded successfully!');
      setTimeout(() => onComplete(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      <h2 className="text-2xl font-bold mb-2">RFC Controls</h2>
      <p className="text-gray-600 mb-6">Return for Credit - Stock Replacement or Credit Value</p>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Supplier and Type */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Supplier *
            </label>
            <select
              name="supplier"
              value={formData.supplier}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Supplier</option>
              {suppliers.map((s: any) => (
                <option key={s.id} value={s.account_number}>
                  {s.name} ({s.account_number})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              RFC Type *
            </label>
            <select
              name="rfc_type"
              value={formData.rfc_type}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {rfcTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Return Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Return Date *
          </label>
          <input
            type="date"
            name="return_date"
            value={formData.return_date}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Stock Item Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stock Code/Item *
            </label>
            <input
              type="text"
              name="stock_item"
              value={formData.stock_item}
              onChange={handleInputChange}
              required
              placeholder="Enter stock code"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantity *
            </label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleInputChange}
              required
              placeholder="0"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Reason */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason for Return
          </label>
          <select
            name="reason"
            value={formData.reason}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Reason</option>
            <option value="DEFECTIVE">Defective Item</option>
            <option value="DAMAGED">Damaged</option>
            <option value="WRONG_ITEM">Wrong Item Received</option>
            <option value="EXCESS_STOCK">Excess Stock</option>
            <option value="UNSALEABLE">Unsaleable</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        {/* Additional Reference */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Reference
          </label>
          <textarea
            name="additional_reference"
            value={formData.additional_reference}
            onChange={handleInputChange}
            rows={3}
            placeholder="Any additional information or comments"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* RFC Info Box */}
        <div className="border-t pt-6 bg-pink-50 p-4 rounded-lg border border-pink-200">
          <h3 className="font-semibold text-gray-900 mb-2">RFC Options:</h3>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• <strong>Stock Replacement:</strong> Stock transferred back to normal file</li>
            <li>• <strong>Credit Granted:</strong> Stock transferred and credit note issued</li>
            <li>• <strong>View Status:</strong> Check RFC status by item or supplier</li>
            <li>• <strong>Value Report:</strong> Total value of all stock on RFC</li>
          </ul>
        </div>

        {/* Buttons */}
        <div className="flex gap-4 pt-6 border-t">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Processing...' : 'Record RFC Transaction'}
          </button>
          <button
            type="button"
            onClick={onComplete}
            className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-900 font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
