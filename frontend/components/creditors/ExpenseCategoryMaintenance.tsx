'use client';

import React, { useState, useEffect } from 'react';
import { ExpenseCategory, useCreditorsAPI } from '@/lib/creditorsApi';
import ExpenseCategoryForm from './ExpenseCategoryForm';

export default function ExpenseCategoryMaintenance() {
  const api = useCreditorsAPI();
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<ExpenseCategory | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [filterActive, setFilterActive] = useState<boolean | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    console.log('Categories state updated:', categories);
  }, [categories]);

  const loadCategories = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading expense categories...');
      const data = await api.listExpenseCategories();
      console.log('Loaded categories:', data);
      // Handle paginated response - extract results array
      const categoriesArray = (data as any).results ? (data as any).results : (Array.isArray(data) ? data : []);
      console.log('Extracted categories array:', categoriesArray);
      setCategories(categoriesArray);
    } catch (err: any) {
      console.error('Failed to load categories:', err);
      setError('Failed to load expense categories');
      setCategories([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this expense category?')) return;

    try {
      await api.deleteExpenseCategory(id);
      setCategories(categories.filter(c => c.id !== id));
      alert('Expense category deleted successfully');
    } catch (err: any) {
      console.error('Failed to delete category:', err);
      alert(`Failed to delete: ${err.message}`);
    }
  };

  const handleFormSuccess = async () => {
    console.log('Form submission successful, reloading categories...');
    setShowForm(false);
    setSelectedCategory(null);
    // Add a small delay to ensure backend has committed the data
    await new Promise(resolve => setTimeout(resolve, 500));
    // Wait for categories to reload
    await loadCategories();
    console.log('Categories reloaded after form success');
  };

  const handleEdit = (category: ExpenseCategory) => {
    setSelectedCategory(category);
    setShowForm(true);
  };

  const handleCreateNew = () => {
    setSelectedCategory(null);
    setShowForm(true);
  };

  // Filter and search categories
  let filteredCategories: ExpenseCategory[] = Array.isArray(categories) ? categories : [];

  if (filterActive !== null) {
    filteredCategories = filteredCategories.filter(c => c.is_active === filterActive);
  }

  if (searchQuery) {
    filteredCategories = filteredCategories.filter(c =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.number?.toString() ?? '').includes(searchQuery)
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Expense Categories</h2>
        <button
          onClick={handleCreateNew}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          + New Category
        </button>
      </div>

      {/* Form Section */}
      {showForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">
            {selectedCategory ? 'Edit Expense Category' : 'Create New Expense Category'}
          </h3>
          <ExpenseCategoryForm
            category={selectedCategory || undefined}
            onSuccess={handleFormSuccess}
            onCancel={() => {
              setShowForm(false);
              setSelectedCategory(null);
            }}
          />
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow p-4 space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search by name or number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filterActive === null ? '' : filterActive ? 'active' : 'inactive'}
            onChange={(e) => {
              if (e.target.value === '') setFilterActive(null);
              else if (e.target.value === 'active') setFilterActive(true);
              else setFilterActive(false);
            }}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Categories List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-4 py-3">
            {error}
          </div>
        )}

        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading categories...</div>
        ) : filteredCategories.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No expense categories found
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Number</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Name</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">MTD</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">YTD</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCategories.map((category) => (
                <tr key={category.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{category.number}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{category.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {category.category_type === 'BOTH' && 'Both'}
                    {category.category_type === 'CASHBOOK' && 'Cash Book Only'}
                    {category.category_type === 'CREDITORS' && 'Creditors Only'}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {(parseFloat(category.total_mtd as any) || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {(parseFloat(category.total_ytd as any) || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        category.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {category.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-center">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => handleEdit(category)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => category.id && handleDelete(category.id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
