'use client';

import { Plus } from 'lucide-react';

interface CreditorsFiltersProps {
  searchQuery: string;
  filterActive: boolean | null;
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFilterChange: (value: string) => void;
  onApplyFilters: () => void;
  onNewCreditor: () => void;
}

export default function CreditorsFilters({
  searchQuery,
  filterActive,
  onSearchChange,
  onFilterChange,
  onApplyFilters,
  onNewCreditor,
}: CreditorsFiltersProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-[250px]">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Creditors
          </label>
          <input
            type="text"
            placeholder="Search by name or account number..."
            value={searchQuery}
            onChange={onSearchChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="w-40">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={filterActive === null ? 'all' : filterActive ? 'active' : 'inactive'}
            onChange={(e) => onFilterChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        <div className="flex gap-2 items-end">
          <button
            onClick={onApplyFilters}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Apply Filters
          </button>
          <button
            onClick={onNewCreditor}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
          >
            <Plus size={20} />
            New Creditor
          </button>
        </div>
      </div>
    </div>
  );
}
