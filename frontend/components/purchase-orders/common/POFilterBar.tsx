'use client';

import React from 'react';
import { Search, X } from 'lucide-react';

interface POFilterBarProps {
  onSearch: (filters: Record<string, string>) => void;
  onReset?: () => void;
}

export function POFilterBar({ onSearch, onReset }: POFilterBarProps) {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('all');
  const [hasFilters, setHasFilters] = React.useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const filters: Record<string, string> = {};
    if (searchTerm) filters.search = searchTerm;
    if (statusFilter !== 'all') filters.status = statusFilter;
    setHasFilters(searchTerm !== '' || statusFilter !== 'all');
    onSearch(filters);
  };

  const handleReset = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setHasFilters(false);
    if (onReset) onReset();
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm p-4">
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          <div className="flex gap-3 w-full md:w-auto flex-1">
            <div className="relative flex-1 md:w-80">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search orders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="all">All Status</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="ISSUED">Issued</option>
              <option value="PARTIALLY_RECEIVED">Partially Received</option>
              <option value="RECEIVED">Received</option>
              <option value="CLOSED">Closed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div className="flex gap-2 w-full md:w-auto">
            <button
              type="submit"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors text-sm"
            >
              <Search className="w-4 h-4" />
              Search
            </button>
            {hasFilters && (
              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-medium transition-colors text-sm"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
