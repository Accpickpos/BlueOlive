'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, AlertCircle, CheckCircle2 } from 'lucide-react';
import cashBookApi from '@/lib/cashBookApi';
import { IncomeCategory } from '@/lib/types/cashBook';

export default function IncomeCategoriesPage() {
  const [categories, setCategories] = useState<IncomeCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [formData, setFormData] = useState<Partial<IncomeCategory>>({
    name: '',
    code: '',
    description: '',
    is_active: true,
  });

  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await cashBookApi.incomeCategories.list();
      setCategories(response.results || []);
    } catch (err) {
      setError('Failed to load income categories');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const validateCategoryCode = (code: string): boolean => {
    // Validate against Chart of Accounts format (e.g., 4000-4999 for income)
    const codeRegex = /^[0-9]{4,}$/;
    if (!codeRegex.test(code)) {
      setValidationError('Category code must be numeric (e.g., 4100)');
      return false;
    }

    const codeNum = parseInt(code);
    if (codeNum < 4000 || codeNum > 4999) {
      setValidationError('Income categories must be in range 4000-4999 (Chart of Accounts)');
      return false;
    }

    // Check for duplicates
    if (!editingId && categories.some(c => c.code === code)) {
      setValidationError('This category code already exists');
      return false;
    }

    setValidationError('');
    return true;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));

    // Validate code as user types
    if (name === 'code') {
      validateCategoryCode(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.name?.trim() || !formData.code?.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    if (!validateCategoryCode(formData.code)) {
      return;
    }

    setLoading(true);

    try {
      if (editingId) {
        await cashBookApi.incomeCategories.update(editingId, formData);
        setSuccess('Income category updated successfully!');
      } else {
        await cashBookApi.incomeCategories.create(formData);
        setSuccess('Income category created successfully!');
      }

      // Reset form
      setFormData({
        name: '',
        code: '',
        description: '',
        is_active: true,
      });
      setShowForm(false);
      setEditingId(null);

      // Refresh list
      await fetchCategories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save category');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (category: IncomeCategory) => {
    setFormData(category);
    setEditingId(category.id ?? null);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category?')) return;

    setLoading(true);
    setError('');

    try {
      await cashBookApi.incomeCategories.delete(id);
      setSuccess('Category deleted successfully!');
      await fetchCategories();
    } catch (err) {
      setError('Failed to delete category');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: '',
      code: '',
      description: '',
      is_active: true,
    });
    setEditingId(null);
    setShowForm(false);
    setValidationError('');
  };

  const filteredCategories = categories.filter(cat =>
    cat.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cat.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Income Categories</h1>
          <p className="text-gray-600 mt-2">Manage income category codes (4000-4999 range)</p>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-green-800">{success}</p>
          </div>
        )}

        {/* Form Section */}
        {showForm && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <h2 className="text-xl font-bold mb-4">
              {editingId ? 'Edit Income Category' : 'Create New Income Category'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category Code * (4000-4999)
                  </label>
                  <input
                    type="text"
                    name="code"
                    value={formData.code || ''}
                    onChange={handleInputChange}
                    placeholder="e.g., 4100"
                    required
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
                      validationError ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
                    }`}
                  />
                  {validationError && (
                    <p className="text-red-600 text-sm mt-1">{validationError}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name || ''}
                    onChange={handleInputChange}
                    placeholder="e.g., Service Income"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description || ''}
                  onChange={handleInputChange}
                  placeholder="Optional description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active || false}
                  onChange={handleInputChange}
                  className="w-4 h-4 border-gray-300 rounded"
                />
                <label className="text-sm font-medium text-gray-700">
                  Active
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading || !!validationError}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? 'Saving...' : editingId ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-4 py-2 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Search and Add Button */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              New Category
            </button>
          )}
        </div>

        {/* Categories Grid */}
        {loading && !showForm ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Loading categories...</p>
          </div>
        ) : filteredCategories.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <p className="text-gray-500">No income categories found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCategories.map(category => (
              <div key={category.id} className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500 hover:shadow-lg transition">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-sm text-gray-600 font-mono">{category.code}</p>
                    <h3 className="text-lg font-bold text-gray-900">{category.name}</h3>
                  </div>
                  {category.is_active && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                      Active
                    </span>
                  )}
                </div>

                {category.description && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{category.description}</p>
                )}

                <div className="flex gap-2 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleEdit(category)}
                    className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 font-medium text-sm flex items-center justify-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => category.id && handleDelete(category.id)}
                    className="flex-1 px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 font-medium text-sm flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        <div className="mt-8 bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">
            Showing {filteredCategories.length} of {categories.length} categories
          </p>
        </div>
      </div>
    </div>
  );
}
