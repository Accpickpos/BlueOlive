'use client';

import { Card } from '@/components/ui/card';
import type { AgeAnalysis } from '@/lib/types/debtors';

interface AgeAnalysisDisplayProps {
  ageAnalysis: AgeAnalysis;
}

export default function AgeAnalysisDisplay({ ageAnalysis }: AgeAnalysisDisplayProps) {
  const COLORS = {
    current: { bg: 'bg-green-100', text: 'text-green-800' },
    30: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
    60: { bg: 'bg-orange-100', text: 'text-orange-800' },
    90: { bg: 'bg-orange-200', text: 'text-orange-900' },
    120: { bg: 'bg-red-100', text: 'text-red-800' },
  };

  return (
    <Card className="p-4 space-y-4">
      <div>
        <h3 className="text-sm font-bold text-gray-700 mb-4">Aging Analysis</h3>
        <div className="space-y-3">
          {ageAnalysis.buckets.map((bucket, idx) => (
            <div key={idx}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-medium">{bucket.label}</span>
                <span className="text-xs font-bold">${bucket.amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${(bucket.amount / ageAnalysis.total_balance) * 100}%`,
                  }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">{bucket.percentage?.toFixed(1)}%</div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t pt-4">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-semibold">Total Balance</span>
          <span className="text-sm font-bold text-blue-600">
            ${ageAnalysis.total_balance?.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </span>
        </div>
        {ageAnalysis.credit_limit && (
          <div className="flex justify-between mb-2">
            <span className="text-sm font-semibold">Credit Limit</span>
            <span className="text-sm">${ageAnalysis.credit_limit?.toLocaleString()}</span>
          </div>
        )}
        {ageAnalysis.utilization_percentage && (
          <div className="flex justify-between">
            <span className="text-sm font-semibold">Credit Used</span>
            <span className="text-sm font-bold text-orange-600">
              {ageAnalysis.utilization_percentage?.toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {ageAnalysis.days_sales_outstanding && (
        <div className="bg-blue-50 p-3 rounded">
          <p className="text-xs text-gray-600">Days Sales Outstanding</p>
          <p className="text-2xl font-bold text-blue-600">{ageAnalysis.days_sales_outstanding?.toFixed(0)}</p>
          <p className="text-xs text-gray-600 mt-1">days to collect</p>
        </div>
      )}
    </Card>
  );
}
