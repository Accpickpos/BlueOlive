'use client';

import { useState, useEffect } from 'react';
import debtorsApi from '@/lib/debtorsApi';
import { getApiErrorMessage } from '@/lib/api';
import type { AgeAnalysis } from '@/lib/types/debtors';

interface DebtorOption {
  id: number;
  name: string;
  current_balance: number;
  dintflag: string | boolean;
}

// DebtorService.calculate_interest's start_period buckets (2=30 days
// onward .. 7=180 days only) — matches the aged buckets returned by
// GET /api/v1/debtors/{id}/age_analysis/ (index 0 = Current, which is
// never chargeable — the manual only charges interest on overdue balances).
const CHARGE_PERIODS = [
  { value: 2, label: '30 Days & Older' },
  { value: 3, label: '60 Days & Older' },
  { value: 4, label: '90 Days & Older' },
  { value: 5, label: '120 Days & Older' },
  { value: 6, label: '150 Days & Older' },
  { value: 7, label: '180 Days Only' },
];

export default function InterestChargingForm() {
  const [debtorId, setDebtorId] = useState<number>(0);
  const [rate, setRate] = useState('1.0');
  const [startPeriod, setStartPeriod] = useState(2);
  const [chargeCreditBalances, setChargeCreditBalances] = useState(false);
  const [calculationDate, setCalculationDate] = useState(new Date().toISOString().split('T')[0]);

  const [debtors, setDebtors] = useState<DebtorOption[]>([]);
  const [loadingDebtors, setLoadingDebtors] = useState(true);
  const [ageAnalysis, setAgeAnalysis] = useState<AgeAnalysis | null>(null);
  const [loadingAgeAnalysis, setLoadingAgeAnalysis] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    debtorsApi.accounts
      .list()
      .then((response) => {
        setDebtors(
          (response.results || []).map((d: any) => ({
            id: d.id,
            name: d.name,
            current_balance: d.total_balance ?? d.dcrnt ?? 0,
            dintflag: d.interest_flag ?? d.dintflag ?? 'N',
          }))
        );
      })
      .catch(() => console.error('Failed to load debtors'))
      .finally(() => setLoadingDebtors(false));
  }, []);

  useEffect(() => {
    if (!debtorId) {
      setAgeAnalysis(null);
      return;
    }
    setLoadingAgeAnalysis(true);
    debtorsApi.accounts
      .getAgeAnalysis(debtorId)
      .then(setAgeAnalysis)
      .catch(() => setAgeAnalysis(null))
      .finally(() => setLoadingAgeAnalysis(false));
  }, [debtorId]);

  const selectedDebtor = debtors.find(d => d.id === debtorId) || null;
  const chargesInterest = selectedDebtor && (selectedDebtor.dintflag === 'Y' || selectedDebtor.dintflag === true);

  // Preview only — the authoritative amount is computed server-side by
  // DebtorService.calculate_interest at submit time from the same buckets.
  const previewInterest = () => {
    if (!ageAnalysis?.buckets?.length) return 0;
    const startIndex = startPeriod - 1; // bucket 0 = Current, never charged
    const buckets = ageAnalysis.buckets.slice(startIndex);
    const base = buckets.reduce((sum, b) => {
      if (!chargeCreditBalances && b.amount < 0) return sum;
      return sum + b.amount;
    }, 0);
    return (base * (parseFloat(rate) || 0)) / 100;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!debtorId || !rate) {
        setError('Please select a debtor and interest rate');
        setLoading(false);
        return;
      }

      const trans = await debtorsApi.transactions.chargeInterest({
        debtor_id: debtorId,
        transaction_date: calculationDate,
        rate: (parseFloat(rate) || 0) / 100,
        start_period: startPeriod,
        charge_credit_balances: chargeCreditBalances,
      });

      setSuccess(`Interest charge of R${Number((trans as any).total_amount ?? previewInterest()).toFixed(2)} posted successfully`);
      setDebtorId(0);
      setRate('1.0');
      setStartPeriod(2);
      setChargeCreditBalances(false);
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to charge interest'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">
          {success}
        </div>
      )}

      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
        Manual §2.2 "Interest Charging": this should only be done at month end after a backup.
      </div>

      {/* Debtor Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Debtor <span className="text-red-500">*</span>
        </label>
        <select
          value={debtorId}
          onChange={(e) => setDebtorId(parseInt(e.target.value) || 0)}
          disabled={loadingDebtors}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        >
          <option value="">Select a debtor...</option>
          {debtors.map(debtor => (
            <option key={debtor.id} value={debtor.id}>
              {debtor.name} (Balance: R{debtor.current_balance.toFixed(2)})
            </option>
          ))}
        </select>
        {selectedDebtor && !chargesInterest && (
          <p className="text-xs text-orange-600 mt-1">
            This debtor is not flagged to charge interest (Charge Interest = No on the account).
          </p>
        )}
      </div>

      {/* Aged Balance Preview */}
      {debtorId > 0 && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm font-medium text-gray-700 mb-2">Aged Balance</p>
          {loadingAgeAnalysis ? (
            <p className="text-sm text-gray-500">Loading...</p>
          ) : (
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-2 text-xs">
              {ageAnalysis?.buckets?.map((bucket, idx) => (
                <div
                  key={bucket.label}
                  className={`p-2 rounded border ${idx >= startPeriod - 1 ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'}`}
                >
                  <p className="text-gray-500">{bucket.label}</p>
                  <p className="font-semibold">R{bucket.amount.toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Interest Rate */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Interest Rate (% per month) <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          step="0.01"
          value={rate}
          onChange={(e) => setRate(e.target.value)}
          placeholder="1.0"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Charge Period */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Charge Interest On <span className="text-red-500">*</span>
        </label>
        <select
          value={startPeriod}
          onChange={(e) => setStartPeriod(parseInt(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {CHARGE_PERIODS.map(period => (
            <option key={period.value} value={period.value}>{period.label}</option>
          ))}
        </select>
      </div>

      {/* Credit Balances */}
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={chargeCreditBalances}
          onChange={(e) => setChargeCreditBalances(e.target.checked)}
          className="rounded"
        />
        <span className="text-sm text-gray-700">Pay Interest on Credit Balances</span>
      </label>

      {/* Calculated Interest Preview */}
      {debtorId > 0 && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-lg font-semibold text-green-700">
            Estimated Interest: R{previewInterest().toFixed(2)}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Final amount is computed server-side from the debtor's current aged balances at posting time.
          </p>
        </div>
      )}

      {/* Calculation Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Calculation Date
        </label>
        <input
          type="date"
          value={calculationDate}
          onChange={(e) => setCalculationDate(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Submit Button */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Charging Interest...' : 'Charge Interest'}
        </button>
      </div>
    </form>
  );
}
