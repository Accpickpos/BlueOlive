'use client';

import React, { useState, useEffect } from 'react';
import { ExpenseCategory, ExpenseCategoryCreateData, useCreditorsAPI } from '@/lib/creditorsApi';

interface ExpenseCategoryFormProps {
  category?: ExpenseCategory;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function ExpenseCategoryForm({ category, onSuccess, onCancel }: ExpenseCategoryFormProps) {
  const api = useCreditorsAPI();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<ExpenseCategoryCreateData>({
    number: category?.number || 0,
    name: category?.name || '',
    category_type: category?.category_type || 'BOTH',
    is_active: category?.is_active !== false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('Submitting expense category:', formData);
      
      if (category?.id) {
        await api.updateExpenseCategory(category.id, formData);
        console.log('Expense category updated successfully');
      } else {
        const result = await api.createExpenseCategory(formData);
        console.log('Expense category created successfully:', result);
      }
      
      console.log('Calling onSuccess callback...');
      onSuccess();
    } catch (err: any) {
      console.error('Failed to save expense category:', err);
      setError(err.message || 'Failed to save expense category');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Category Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category Number *
          </label>
          <input
            type="number"
            name="number"
            min="1"
            max="99999999"
            value={formData.number}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter category number (1-99999999)"
          />
        </div>

        {/* Category Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category Name *
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            maxLength={100}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter category name"
          />
        </div>

        {/* Category Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category Type
          </label>
          <select
            name="category_type"
            value={formData.category_type || 'BOTH'}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="BOTH">Both Cash Book & Creditors</option>
            <option value="CASHBOOK">Cash Book Only</option>
            <option value="CREDITORS">Creditors Only</option>
          </select>
        </div>

        {/* Active Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Active</span>
          </label>
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex gap-2 pt-4 border-t">
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : category ? 'Update Category' : 'Create Category'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
