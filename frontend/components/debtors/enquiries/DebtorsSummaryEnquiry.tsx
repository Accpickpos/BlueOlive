'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';
import SummaryStatistics from './SummaryStatistics';
import AgingChart from './AgingChart';
import AgeAnalysisDisplay from './AgeAnalysisDisplay';
import type { DebtorsSummary, AgeAnalysis } from '@/lib/types/debtors';

export default function DebtorsSummaryEnquiry() {
  const [cutoffDate, setCutoffDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [summary, setSummary] = useState<DebtorsSummary | null>(null);
  const [ageAnalysis, setAgeAnalysis] = useState<AgeAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const generateReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (cutoffDate) {
        params.append('cutoff_date', cutoffDate);
      }

      // Fetch summary data
      const summaryResponse = await apiRequest(
        `/api/v1/debtors/summary/?${params}`
      );
      const summaryData = (summaryResponse as any).data || summaryResponse;
      setSummary(summaryData);

      // Fetch age analysis data
      const ageResponse = await apiRequest(
        `/api/v1/debtors/age-analysis/?${params}`
      );
      const ageData = (ageResponse as any).data || ageResponse;
      setAgeAnalysis(ageData);
    } catch (err) {
      setError('Failed to load debtors summary');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    generateReport();
  }, []);

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-900">
        Total Debtors Summary - Age Analysis & Control Enquiry
      </h2>

      {/* Filters */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 space-y-4">
        <h3 className="font-semibold text-gray-900">Report Filters</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cutoff Date
            </label>
            <input
              type="date"
              value={cutoffDate}
              onChange={(e) => setCutoffDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={generateReport}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium"
            >
              {loading ? 'Loading...' : 'Generate Report'}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Summary Statistics */}
      {summary && (
        <div>
          <SummaryStatistics summary={summary} />
        </div>
      )}

      {/* Charts and Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Aging Chart */}
        {summary && (
          <div>
            <AgingChart summary={summary} />
          </div>
        )}

        {/* Age Analysis Display */}
        {ageAnalysis && (
          <div>
            <AgeAnalysisDisplay ageAnalysis={ageAnalysis} />
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading summary data...</p>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!summary && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-600">Click "Generate Report" to view debtors summary</p>
        </div>
      )}
    </div>
  );
}
