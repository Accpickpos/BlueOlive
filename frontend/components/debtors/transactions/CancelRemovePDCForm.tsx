'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';

interface PDCRecord {
  id: number;
  debtor_id: number;
  debtor_name: string;
  cheque_number: string;
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
  const [loadingPDCs, setLoadingPDCs] = useState(true);

  useEffect(() => {
    loadPDCRecords();
  }, []);

  const loadPDCRecords = async () => {
    try {
      // Load unprocessed PDC records - try without query param first to debug
      const response = await apiRequest('/api/debtors/post-dated-cheques/');
      let pdcs: PDCRecord[] = [];
      
      if ((response as any).results) {
        // Filter for unprocessed PDCs on frontend
        pdcs = (response as any).results
          .filter((pdc: any) => !pdc.is_processed)
          .map((pdc: any) => ({
            id: pdc.id,
            debtor_id: pdc.debtor,
            debtor_name: pdc.debtor_name || `Debtor ${pdc.debtor}`,
            cheque_number: pdc.reference,
            amount: parseFloat(pdc.amount),
            pdc_date: pdc.cheque_date,
            posting_date: pdc.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
          }));
      } else if (Array.isArray(response)) {
        pdcs = response.filter(p => !p.is_processed);
      }
      
      setPdcRecords(pdcs);
    } catch (err) {
      console.error('Failed to load PDC records:', err);
      // For now, show empty list if endpoint doesn't exist
      setPdcRecords([]);
    } finally {
      setLoadingPDCs(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (name === 'pdc_id') {
      const pdc = pdcRecords.find(p => p.id === parseInt(value));
      setSelectedPDC(pdc || null);
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

      const response = await apiRequest(
        `/api/debtors/post-dated-cheques/${formData.pdc_id}/cancel/`,
        {
          method: 'POST',
          body: {
            cancellation_reason: formData.cancellation_reason,
            cancellation_date: formData.cancellation_date,
            notes: formData.notes,
          }
        }
      );

      setSuccess(`PDC (Cheque #${selectedPDC?.cheque_number}) cancelled successfully`);
      setFormData({
        pdc_id: 0,
        cancellation_reason: 'CUSTOMER_REQUEST',
        cancellation_date: new Date().toISOString().split('T')[0],
        notes: '',
      });
      setSelectedPDC(null);
      loadPDCRecords();
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

      {/* Info Alert */}
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
        <p className="font-medium mb-1">⚠️ Warning</p>
        <p>Cancelling a PDC will reverse the transaction. Ensure you have the correct authorization before proceeding.</p>
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
          disabled={loadingPDCs}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        >
          <option value="">Select a PDC...</option>
          {pdcRecords.map(pdc => (
            <option key={pdc.id} value={pdc.id}>
              {pdc.debtor_name} - Cheque #{pdc.cheque_number} - R{pdc.amount.toFixed(2)} ({pdc.pdc_date})
            </option>
          ))}
        </select>
        {pdcRecords.length === 0 && !loadingPDCs && (
          <p className="text-xs text-gray-500 mt-2">No pending PDCs available</p>
        )}
      </div>

      {/* PDC Details */}
      {selectedPDC && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Debtor:</p>
              <p className="font-medium">{selectedPDC.debtor_name}</p>
            </div>
            <div>
              <p className="text-gray-600">Cheque Number:</p>
              <p className="font-medium">{selectedPDC.cheque_number}</p>
            </div>
            <div>
              <p className="text-gray-600">Amount:</p>
              <p className="font-medium">R{selectedPDC.amount.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">PDC Date:</p>
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

      {/* Submit Button */}
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
