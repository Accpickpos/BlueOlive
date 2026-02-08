'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, Plus, Trash2 } from 'lucide-react';
import { useCreditorsAPI } from '@/lib/creditorsApi';
import creditorsApi from '@/lib/creditorsApi';

interface LineItem {
  id: string;
  stock_item: string;
  quantity: number;
  unit_cost: number;
  tax_code: number;
}

interface ReturnsStockFormProps {
  onComplete: () => void;
}

export default function ReturnsStockForm({ onComplete }: ReturnsStockFormProps) {
  const { listSuppliers } = useCreditorsAPI();
  
  const [formData, setFormData] = useState({
    supplier: '',
    document_date: new Date().toISOString().split('T')[0],
    document_number: '',
    inclusive_of_vat: false,
    additional_reference: '',
  });

  const [lineItems, setLineItems] = useState<LineItem[]>([
    { id: '1', stock_item: '', quantity: 0, unit_cost: 0, tax_code: 1 },
  ]);

  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    });
  };

  const handleLineItemChange = (index: number, field: string, value: any) => {
    const updatedItems = [...lineItems];
    updatedItems[index] = {
      ...updatedItems[index],
      [field]: value,
    };
    setLineItems(updatedItems);
  };

  const addLineItem = () => {
    setLineItems([
      ...lineItems,
      {
        id: Date.now().toString(),
        stock_item: '',
        quantity: 0,
        unit_cost: 0,
        tax_code: 1,
      },
    ]);
  };

  const removeLineItem = (index: number) => {
    if (lineItems.length > 1) {
      setLineItems(lineItems.filter((_, i) => i !== index));
    }
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

      if (lineItems.some(item => !item.stock_item || item.quantity === 0)) {
        throw new Error('Please complete all line items');
      }

      const payload = {
        ...formData,
        line_items: lineItems.map(item => ({
          stock_item: item.stock_item,
          quantity: parseFloat(item.quantity.toString()),
          unit_cost: parseFloat(item.unit_cost.toString()),
          tax_code: parseInt(item.tax_code.toString()),
        })),
      };

      const response = await creditorsApi.rfc.create(payload);

      if (!response) {
        throw new Error('Failed to create transaction');
      }

      setSuccess('Stock return recorded successfully!');
      setTimeout(() => onComplete(), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl">
      <h2 className="text-2xl font-bold mb-2">Returns - Stock Items</h2>
      <p className="text-gray-600 mb-6">Credit Note or Goods Returned Note</p>

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
        {/* Header Section */}
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
              Document Date *
            </label>
            <input
              type="date"
              name="document_date"
              value={formData.document_date}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Credit Note Number *
            </label>
            <input
              type="text"
              name="document_number"
              value={formData.document_number}
              onChange={handleInputChange}
              required
              placeholder="Supplier's credit note number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <input
                type="checkbox"
                name="inclusive_of_vat"
                checked={formData.inclusive_of_vat}
                onChange={handleInputChange}
                className="rounded"
              />
              Inclusive of VAT
            </label>
          </div>
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
            rows={2}
            placeholder="Any additional information"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Line Items */}
        <div className="border-t pt-6">
          <h3 className="font-semibold text-gray-900 mb-4">Returned Items</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Stock Code</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Quantity Returned</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Unit Cost</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Tax Code</th>
                  <th className="px-3 py-2 text-center font-medium text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {lineItems.map((item, index) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={item.stock_item}
                        onChange={(e) =>
                          handleLineItemChange(index, 'stock_item', e.target.value)
                        }
                        placeholder="Enter stock code"
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) =>
                          handleLineItemChange(index, 'quantity', parseFloat(e.target.value))
                        }
                        placeholder="0"
                        step="0.01"
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        value={item.unit_cost}
                        onChange={(e) =>
                          handleLineItemChange(index, 'unit_cost', parseFloat(e.target.value))
                        }
                        placeholder="0.00"
                        step="0.01"
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <select
                        value={item.tax_code}
                        onChange={(e) =>
                          handleLineItemChange(index, 'tax_code', parseInt(e.target.value))
                        }
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value={1}>VAT (14%)</option>
                        <option value={2}>No VAT</option>
                      </select>
                    </td>
                    <td className="px-3 py-2 text-center">
                      {lineItems.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeLineItem(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            type="button"
            onClick={addLineItem}
            className="mt-3 flex items-center gap-2 px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Line Item
          </button>
        </div>

        {/* Buttons */}
        <div className="flex gap-4 pt-6 border-t">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Processing...' : 'Record Return'}
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
