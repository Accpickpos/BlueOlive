'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import SummaryCards from '@/components/debtors/dashboard/SummaryCards';
import AgeAnalysisChart from '@/components/debtors/dashboard/AgeAnalysisChart';
import QuickLinks from '@/components/debtors/dashboard/QuickLinks';

export default function DebtorsDashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['debtors-summary'],
    queryFn: () => debtorsApi.summary.get(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Debtors Management</h1>
          <p className="text-gray-600 mt-1">Track receivables, manage accounts, and monitor aging</p>
        </div>
      </div>

      {/* Summary Cards */}
      {!summaryLoading && summary && (
        <SummaryCards summary={summary} />
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Age Analysis Chart - Full width on left */}
        <div className="lg:col-span-2">
          {!summaryLoading && summary && (
            <AgeAnalysisChart summary={summary} />
          )}
        </div>

        {/* Quick Links */}
        <div className="lg:col-span-1">
          <QuickLinks />
        </div>
      </div>

      {/* Additional Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">Credit Utilization</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Total Receivable</span>
                <span className="font-bold">${summary.total_receivable?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min((summary.total_receivable! / summary.total_credit_limit!) * 100, 100)}%`,
                  }}
                />
              </div>
              <div className="text-xs text-gray-600">
                {summary.utilization_percentage?.toFixed(1)}% of ${summary.total_credit_limit?.toLocaleString('en-US', { maximumFractionDigits: 2 })} limit
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">Aging Overview</h3>
            <div className="space-y-2">
              <div className="text-xs space-y-1">
                <div className="flex justify-between">
                  <span>Current:</span>
                  <span className="font-semibold">${summary.aging_summary?.current?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-orange-600">
                  <span>120+ Days:</span>
                  <span className="font-semibold">${summary.critical_aging?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
