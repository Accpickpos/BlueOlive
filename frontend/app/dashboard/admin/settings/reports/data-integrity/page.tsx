'use client';

import { useState } from 'react';
import { settingsReportsApi, DataIntegrityReport, IntegrityCheckResult } from '@/lib/settings/reports';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

const SECTIONS: { key: keyof DataIntegrityReport; title: string }[] = [
  { key: 'debtors', title: 'Debtor Balances' },
  { key: 'creditors', title: 'Creditor Balances' },
  { key: 'stock', title: 'Stock Quantities' },
];

export default function DataIntegrityPage() {
  const [report, setReport] = useState<DataIntegrityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runCheck() {
    setLoading(true);
    setError(null);
    try {
      const data = await settingsReportsApi.dataIntegrityReport();
      setReport(data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to run integrity check'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/settings">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Data Integrity Report</h1>
          <p className="text-gray-600 mt-1">
            Read-only reconciliation: stored balances vs. transaction history. Detects discrepancies — does not fix them.
          </p>
        </div>
      </div>

      <Card className="p-6">
        <Button onClick={runCheck} disabled={loading}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
          Run Integrity Check
        </Button>
      </Card>

      {error && (
        <div className="rounded p-3 text-sm border bg-red-50 border-red-200 text-red-800">{error}</div>
      )}

      {report &&
        SECTIONS.map(({ key, title }) => {
          const result = report[key] as IntegrityCheckResult | undefined;
          if (!result) return null;
          return (
            <Card key={key} className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold">{title}</h2>
                {result.discrepancy_count === 0 ? (
                  <span className="flex items-center gap-1 text-green-700 text-sm">
                    <CheckCircle2 className="w-4 h-4" /> {result.checked} checked, no discrepancies
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-700 text-sm">
                    <AlertTriangle className="w-4 h-4" /> {result.discrepancy_count} of {result.checked} discrepant
                  </span>
                )}
              </div>
              {result.discrepancies.length > 0 && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left border-b">
                      {Object.keys(result.discrepancies[0]).map((col) => (
                        <th key={col} className="py-2 capitalize">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.discrepancies.map((row, i) => (
                      <tr key={i} className="border-b">
                        {Object.entries(row).map(([col, val]) => (
                          <td key={col} className={`py-2 ${col === 'difference' ? 'text-red-700 font-medium' : ''}`}>
                            {String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          );
        })}
    </div>
  );
}
