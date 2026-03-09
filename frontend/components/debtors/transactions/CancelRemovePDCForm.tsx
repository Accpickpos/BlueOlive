'use client';

import { useState, useEffect } from 'react';
import { debtorsApi } from '@/lib/debtorsApi';
import { apiRequest } from '@/lib/api';

interface DebtorOption {
  id: number;
  name: string;
  account: string;
}

interface PDCRecord {
  id: number;
  debtor_id: number;
  debtor_name: string;
  debtor_account: string;
  amount: number;
  pdc_date: string;
  posting_date: string;
}

interface CancelPDCData {
  pdc_id: number;
  cancellation_reason: string;
  cancellation_date: string;
  notes: string;
}

export default function CancelRemovePDCForm() {
  const [formData, setFormData] = useState<CancelPDCData>({
    pdc_id: 0,
    cancellation_reason: 'CUSTOMER_REQUEST',
    cancellation_date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  const [pdcRecords, setPdcRecords] = useState<PDCRecord[]>([]);
  const [selectedPDC, setSelectedPDC] = useState<PDCRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loadingPDCs, setLoadingPDCs] = useState(false);
  const [debtors, setDebtors] = useState<DebtorOption[]>([]);
  const [selectedDebtorId, setSelectedDebtorId] = useState<number | null>(null);
  const [loadingDebtors, setLoadingDebtors] = useState(true);


  useEffect(() => {
    // Load debtors for selection
    const fetchDebtors = async () => {
      setLoadingDebtors(true);
      try {
        const response = await debtorsApi.accounts.list();
        const options = response.results
          ? response.results.map((d: any) => ({
              id: d.id,
              name: d.name,
              account: d.account_number || '',
            }))
          : [];
        setDebtors(options);
      } catch (err) {
        setError('Failed to load debtors.');
      } finally {
        setLoadingDebtors(false);
      }
    };
    fetchDebtors();
  }, []);

  useEffect(() => {
    if (selectedDebtorId) {
      loadPDCRecords(selectedDebtorId);
    } else {
      setPdcRecords([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDebtorId]);

  const loadPDCRecords = async (debtorId: number) => {
    setLoadingPDCs(true);
    try {
      const response = await debtorsApi.pdcs.list(debtorId);
      let pdcs: PDCRecord[] = [];
      const mapPdc = (pdc: any): PDCRecord => ({
        id: pdc.id,
        debtor_id: pdc.debtor,
        debtor_name: pdc.debtor_name || `Debtor ${pdc.debtor_account || pdc.debtor}`,
        debtor_account: pdc.debtor_account || '',
        amount: parseFloat(pdc.amount),
        pdc_date: pdc.cheque_date,
        posting_date: pdc.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
      });
      if (response.results) {
        pdcs = response.results
          .filter((pdc: any) => pdc.is_active === true)
          .map(mapPdc);
      } else if (Array.isArray(response)) {
        pdcs = (response as any[])
          .filter((pdc: any) => pdc.is_active === true)
          .map(mapPdc);
      }
      setPdcRecords(pdcs);
      setError(pdcs.length === 0 ? 'No post-dated cheques found for this debtor.' : '');
    } catch (err: any) {
      console.error('Failed to load PDC records:', err);
      if (err?.response?.status === 404) {
        setError('No post-dated cheques found or this operation is not supported.');
      } else {
        setError('Failed to load post-dated cheques.');
      }
      setPdcRecords([]);
    } finally {
      setLoadingPDCs(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (name === 'pdc_id') {
      const pdc = pdcRecords.find(p => p.id === parseInt(value));
      setSelectedPDC(pdc || null);
    }
    if (name === 'debtor_id') {
      setSelectedDebtorId(value ? parseInt(value) : null);
      setFormData(prev => ({ ...prev, pdc_id: 0 }));
      setSelectedPDC(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (!formData.pdc_id) {
        setError('Please select a PDC to cancel');
        setLoading(false);
        return;
      }

      await apiRequest(
        `/api/v1/debtors/post-dated-cheques/${formData.pdc_id}/cancel/`,
        {
          method: 'POST',
          body: {
            cancellation_reason: formData.cancellation_reason,
            cancellation_date: formData.cancellation_date,
            notes: formData.notes,
          }
        }
      );

      setSuccess(`PDC #${selectedPDC?.id} for ${selectedPDC?.debtor_name} cancelled successfully`);
      setFormData({
        pdc_id: 0,
        cancellation_reason: 'CUSTOMER_REQUEST',
        cancellation_date: new Date().toISOString().split('T')[0],
        notes: '',
      });
      setSelectedPDC(null);
      if (selectedDebtorId) {
        loadPDCRecords(selectedDebtorId);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to cancel PDC');
    } finally {
      setLoading(false);
    }
  };

  const cancellationReasons = [
    { value: 'CUSTOMER_REQUEST', label: 'Customer Request' },
    { value: 'CHEQUE_LOST', label: 'Cheque Lost/Misplaced' },
    { value: 'CHEQUE_DAMAGED', label: 'Cheque Damaged' },
    { value: 'DISHONOURED', label: 'Cheque Dishonoured' },
    { value: 'DUPLICATE', label: 'Duplicate Entry' },
    { value: 'OTHER', label: 'Other' },
  ];

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

      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
        <p className="font-medium mb-1">⚠️ Warning</p>
        <p>Cancelling a PDC will reverse the transaction. Ensure you have the correct authorization before proceeding.</p>
      </div>

      {/* Debtor Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Debtor <span className="text-red-500">*</span>
        </label>
        <select
          name="debtor_id"
          value={selectedDebtorId ?? ''}
          onChange={handleChange}
          disabled={loadingDebtors}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        >
          <option value="">{loadingDebtors ? 'Loading debtors...' : 'Select a debtor...'}</option>
          {debtors.map(debtor => (
            <option key={debtor.id} value={debtor.id}>
              {debtor.name} {debtor.account ? `(${debtor.account})` : ''}
            </option>
          ))}
        </select>
      </div>

      {/* PDC Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select PDC to Cancel <span className="text-red-500">*</span>
        </label>
        <select
          name="pdc_id"
          value={formData.pdc_id}
          onChange={handleChange}
          disabled={loadingPDCs || !selectedDebtorId}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        >
          <option value="">{!selectedDebtorId ? 'Select a debtor first...' : loadingPDCs ? 'Loading PDCs...' : 'Select a PDC...'}</option>
          {pdcRecords.map(pdc => (
            <option key={pdc.id} value={pdc.id}>
              PDC #{pdc.id} — R{pdc.amount.toFixed(2)} ({pdc.pdc_date})
            </option>
          ))}
        </select>
        {pdcRecords.length === 0 && !loadingPDCs && selectedDebtorId && (
          <p className="text-xs text-gray-500 mt-2">No active PDCs available to cancel for this debtor</p>
        )}
      </div>

      {/* PDC Details */}
      {selectedPDC && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Debtor:</p>
              <p className="font-medium">{selectedPDC.debtor_name}</p>
            </div>
            <div>
              <p className="text-gray-600">Account:</p>
              <p className="font-medium">{selectedPDC.debtor_account || '—'}</p>
            </div>
            <div>
              <p className="text-gray-600">PDC Reference:</p>
              <p className="font-medium">PDC #{selectedPDC.id}</p>
            </div>
            <div>
              <p className="text-gray-600">Amount:</p>
              <p className="font-medium">R{selectedPDC.amount.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Cheque Date:</p>
              <p className="font-medium">{selectedPDC.pdc_date}</p>
            </div>
            <div>
              <p className="text-gray-600">Posting Date:</p>
              <p className="font-medium">{selectedPDC.posting_date}</p>
            </div>
          </div>
        </div>
      )}

      {/* Cancellation Reason */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cancellation Reason <span className="text-red-500">*</span>
        </label>
        <select
          name="cancellation_reason"
          value={formData.cancellation_reason}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {cancellationReasons.map(reason => (
            <option key={reason.value} value={reason.value}>
              {reason.label}
            </option>
          ))}
        </select>
      </div>

      {/* Cancellation Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cancellation Date
        </label>
        <input
          type="date"
          name="cancellation_date"
          value={formData.cancellation_date}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cancellation Notes
        </label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Provide additional details about the cancellation..."
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Submit */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading || !formData.pdc_id}
          className="px-6 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Cancelling PDC...' : 'Cancel PDC'}
        </button>
      </div>
    </form>
  );
}