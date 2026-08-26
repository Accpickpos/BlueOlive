'use client';

import { useState, useCallback, useRef } from 'react';
import { api, getApiErrorMessage } from '@/lib/api';
import { ENDPOINTS } from '@/lib/api-config';

// ============================================================
// Types
// ============================================================
interface Shop {
  id: number;
  name: string;
  code: string;
  schema_name: string;
}

interface TenantWithShops {
  id: number;
  name: string;
  slug: string;
  shops: Shop[];
}

interface AnalysisResult {
  headers: string[];
  total_rows: number;
  sample_rows: string[][];
  suggested_mappings: Record<string, string>;
  available_model_fields: string[];
  delimiter: string;
}

interface ImportResult {
  success: boolean;
  tenant: string;
  shop: string;
  schema: string;
  total_rows: number;
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
  message: string;
}

type ImportMode = 'create_or_update' | 'create_only' | 'update_only';
type Step = 'select' | 'upload' | 'map' | 'importing' | 'done';

// Model field → friendly label
const FIELD_LABELS: Record<string, string> = {
  customer_number: 'Account Number (DNO)',
  name: 'Customer Name',
  short_name: 'Short Name',
  contact_person: 'Contact Person',
  phone: 'Phone',
  phone2: 'Phone 2',
  fax: 'Fax',
  email: 'Email',
  address_line1: 'Address Line 1',
  address_line2: 'Address Line 2',
  address_line3: 'Address Line 3',
  postal_code: 'Postal Code',
  delivery_address1: 'Delivery Address 1',
  delivery_address2: 'Delivery Address 2',
  delivery_address3: 'Delivery Address 3',
  delivery_address4: 'Delivery Address 4',
  tax_number: 'Tax Number',
  vat_reference: 'VAT Reference',
  area_code: 'Sales Area',
  balance_brought_forward: 'Balance B/F',
  balance_current: 'Current Balance',
  balance_30_days: '30 Days',
  balance_60_days: '60 Days',
  balance_90_days: '90 Days',
  balance_120_days: '120 Days',
  balance_150_days: '150 Days',
  balance_180_days: '180 Days',
  sales_month: 'Sales (Month)',
  sales_year: 'Sales (Year)',
  profit_month: 'Profit (Month)',
  profit_year: 'Profit (Year)',
  last_payment_amount: 'Last Payment Amount',
  last_payment_date: 'Last Payment Date',
  discount_percentage: 'Discount %',
  credit_limit: 'Credit Limit',
  interest_flag: 'Charge Interest',
  price_level: 'Price Level',
  account_type: 'Account Type',
  payment_terms: 'Payment Terms',
  prompt_payment_discount: 'Prompt Discount %',
  discount_printable: 'Print Discount',
  positive_balance_only: 'Positive Balance Only',
  block_flag: 'Block Flag',
  date_opened: 'Date Opened',
  notes: 'Notes',
};

export default function DebtorImportPage() {
  // --- State ---
  const [step, setStep] = useState<Step>('select');
  const [tenants, setTenants] = useState<TenantWithShops[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // File & analysis
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  // Mappings: csv_header → model_field | '' (unmapped)
  const [mappings, setMappings] = useState<Record<string, string>>({});

  // Import
  const [importMode, setImportMode] = useState<ImportMode>('create_or_update');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Derived
  const selectedTenant = tenants.find(t => t.id === selectedTenantId) ?? null;
  const shops = selectedTenant?.shops ?? [];
  const selectedShop = shops.find(s => s.id === selectedShopId) ?? null;

  // ============================================================
  // Step 1: Load tenants
  // ============================================================
  const loadTenants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<TenantWithShops[]>(ENDPOINTS.SAAS_ADMIN.IMPORT_TENANTS);
      setTenants(res.data);
      if (res.data.length === 0) {
        setError('No active tenants found. Create a tenant and shop first.');
      }
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to load tenants'));
    } finally {
      setLoading(false);
    }
  }, []);

  // Load tenants on first render
  const [didLoad, setDidLoad] = useState(false);
  if (!didLoad) {
    setDidLoad(true);
    loadTenants();
  }

  // ============================================================
  // Step 2: Upload & analyze
  // ============================================================
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setAnalysis(null);
    setMappings({});
    setImportResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await api.post<AnalysisResult>(ENDPOINTS.SAAS_ADMIN.IMPORT_ANALYZE, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAnalysis(res.data);
      setMappings(res.data.suggested_mappings);
      setStep('map');
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to analyze file'));
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Step 3: Execute import
  // ============================================================
  const handleImport = async () => {
    if (!file || !selectedTenantId || !selectedShopId) return;

    // Filter out unmapped columns
    const activeMappings: Record<string, string> = {};
    for (const [csvCol, field] of Object.entries(mappings)) {
      if (field) activeMappings[csvCol] = field;
    }

    if (!Object.values(activeMappings).includes('customer_number')) {
      setError('You must map a column to "Account Number (DNO)" — it is required.');
      return;
    }

    setStep('importing');
    setLoading(true);
    setError(null);
    setImportResult(null);

    try {
      const form = new FormData();
      form.append('file', file);
      form.append('tenant_id', String(selectedTenantId));
      form.append('shop_id', String(selectedShopId));
      form.append('mappings', JSON.stringify(activeMappings));
      form.append('mode', importMode);

      const res = await api.post<ImportResult>(ENDPOINTS.SAAS_ADMIN.IMPORT_EXECUTE, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImportResult(res.data);
      setStep('done');
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Import failed'));
      setStep('map');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Reset
  // ============================================================
  const handleReset = () => {
    setStep('select');
    setFile(null);
    setAnalysis(null);
    setMappings({});
    setImportResult(null);
    setError(null);
    setImportMode('create_or_update');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ============================================================
  // Render helpers
  // ============================================================
  const mappedCount = Object.values(mappings).filter(Boolean).length;
  const hasCustomerNumber = Object.values(mappings).includes('customer_number');

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Import Debtors from CSV</h1>
      <p className="text-gray-500 mb-6">
        Upload a CSV file and import debtor data into a specific tenant shop schema.
      </p>

      {/* Error banner */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4 text-red-800 flex items-start gap-2">
          <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/></svg>
          <span>{error}</span>
        </div>
      )}

      {/* =============================== */}
      {/* Step indicator */}
      {/* =============================== */}
      <div className="flex items-center gap-1 mb-8">
        {(['select', 'upload', 'map', 'done'] as const).map((s, i) => {
          const labels = ['1. Select Target', '2. Upload CSV', '3. Map & Import', '4. Done'];
          const active = step === s || (step === 'importing' && s === 'map');
          const completed =
            (s === 'select' && ['upload', 'map', 'importing', 'done'].includes(step)) ||
            (s === 'upload' && ['map', 'importing', 'done'].includes(step)) ||
            (s === 'map' && step === 'done');
          return (
            <div key={s} className="flex items-center gap-1 flex-1">
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold border-2 ${
                  completed
                    ? 'bg-green-600 border-green-600 text-white'
                    : active
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-400'
                }`}
              >
                {completed ? '✓' : i + 1}
              </div>
              <span className={`text-sm ${active || completed ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>
                {labels[i]}
              </span>
              {i < 3 && <div className={`flex-1 h-0.5 mx-2 ${completed ? 'bg-green-500' : 'bg-gray-200'}`} />}
            </div>
          );
        })}
      </div>

      {/* =============================== */}
      {/* Step 1: Select Tenant & Shop */}
      {/* =============================== */}
      {step === 'select' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Select Target Tenant &amp; Shop</h2>
          <p className="text-sm text-gray-500">
            Choose which tenant and shop schema to import debtors into.
          </p>

          {loading ? (
            <div className="py-8 text-center text-gray-400">Loading tenants...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Tenant select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tenant</label>
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={selectedTenantId ?? ''}
                  onChange={e => {
                    const id = Number(e.target.value) || null;
                    setSelectedTenantId(id);
                    setSelectedShopId(null);
                  }}
                >
                  <option value="">-- Select tenant --</option>
                  {tenants.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              {/* Shop select */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Shop Schema</label>
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={selectedShopId ?? ''}
                  onChange={e => setSelectedShopId(Number(e.target.value) || null)}
                  disabled={!selectedTenantId}
                >
                  <option value="">-- Select shop --</option>
                  {shops.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.schema_name})
                    </option>
                  ))}
                </select>
                {selectedShop && (
                  <p className="mt-1 text-xs text-gray-400">
                    Schema: <span className="font-mono text-gray-600">{selectedShop.schema_name}</span>
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              disabled={!selectedTenantId || !selectedShopId}
              onClick={() => setStep('upload')}
              className="px-5 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next: Upload CSV →
            </button>
          </div>
        </div>
      )}

      {/* =============================== */}
      {/* Step 2: Upload CSV */}
      {/* =============================== */}
      {step === 'upload' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Upload CSV File</h2>
            <div className="text-sm text-gray-500">
              Target: <strong>{selectedTenant?.name}</strong> → <strong>{selectedShop?.name}</strong>
              <span className="font-mono text-xs text-gray-400 ml-1">({selectedShop?.schema_name})</span>
            </div>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:border-blue-400 transition">
            <svg className="mx-auto h-12 w-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="block mx-auto text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="mt-2 text-xs text-gray-400">CSV files only. Semicolon or comma delimited.</p>
          </div>

          {file && (
            <div className="bg-blue-50 rounded-lg p-3 flex items-center gap-3 text-sm">
              <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/></svg>
              <span className="text-blue-800 font-medium">{file.name}</span>
              <span className="text-blue-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}

          <div className="pt-2 flex justify-between">
            <button
              onClick={() => setStep('select')}
              className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
            >
              ← Back
            </button>
            <button
              disabled={!file || loading}
              onClick={handleAnalyze}
              className="px-5 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-2"
            >
              {loading && <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />}
              Analyze & Map Columns →
            </button>
          </div>
        </div>
      )}

      {/* =============================== */}
      {/* Step 3: Map columns & import */}
      {/* =============================== */}
      {(step === 'map' || step === 'importing') && analysis && (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-wrap items-center gap-4 text-sm">
            <div>
              File: <strong>{file?.name}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Rows: <strong>{analysis.total_rows}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Columns: <strong>{analysis.headers.length}</strong>
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Mapped: <strong className={hasCustomerNumber ? 'text-green-600' : 'text-red-600'}>{mappedCount}</strong>
              / {analysis.headers.length}
            </div>
            <div className="text-gray-400">|</div>
            <div>
              Target: <strong>{selectedTenant?.name}</strong> → <strong>{selectedShop?.name}</strong>
            </div>
          </div>

          {/* Column mapping */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Column Mapping</h2>
              <span className="text-xs text-gray-400">Select which model field each CSV column maps to</span>
            </div>

            <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">CSV Column</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">→ Model Field</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {analysis.headers.map((header, idx) => (
                    <tr key={header} className={mappings[header] ? 'bg-green-50/50' : ''}>
                      <td className="px-4 py-2 font-mono text-xs text-gray-700">{header}</td>
                      <td className="px-4 py-2">
                        <select
                          value={mappings[header] || ''}
                          onChange={e => setMappings(prev => ({ ...prev, [header]: e.target.value }))}
                          className={`w-full rounded border px-2 py-1 text-xs ${
                            mappings[header] === 'customer_number'
                              ? 'border-green-500 bg-green-50 font-bold'
                              : mappings[header]
                              ? 'border-green-300'
                              : 'border-gray-300'
                          }`}
                        >
                          <option value="">-- skip --</option>
                          {(analysis.available_model_fields || []).map(field => (
                            <option key={field} value={field}>
                              {FIELD_LABELS[field] || field}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-400 max-w-xs truncate">
                        {analysis.sample_rows.slice(0, 3).map(r => r[idx] ?? '').join(' | ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Import options */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Import Mode</h3>
            <div className="flex gap-4 flex-wrap">
              {([
                { value: 'create_or_update', label: 'Create or Update', desc: 'Upsert: create new, update existing' },
                { value: 'create_only', label: 'Create Only', desc: 'Skip rows that already exist' },
                { value: 'update_only', label: 'Update Only', desc: 'Only update existing records' },
              ] as const).map(opt => (
                <label
                  key={opt.value}
                  className={`flex items-start gap-2 border rounded-lg p-3 cursor-pointer transition ${
                    importMode === opt.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="mode"
                    checked={importMode === opt.value}
                    onChange={() => setImportMode(opt.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <div className="text-sm font-medium text-gray-800">{opt.label}</div>
                    <div className="text-xs text-gray-400">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center">
            <button
              onClick={() => { setStep('upload'); setAnalysis(null); setMappings({}); }}
              className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition"
              disabled={step === 'importing'}
            >
              ← Back
            </button>
            <button
              disabled={!hasCustomerNumber || step === 'importing' || loading}
              onClick={handleImport}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-green-600 hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-2"
            >
              {step === 'importing' ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  Importing...
                </>
              ) : (
                <>
                  Import {analysis.total_rows} Rows →
                </>
              )}
            </button>
          </div>

          {/* Warning if customer_number not mapped */}
          {!hasCustomerNumber && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-amber-800 text-sm flex items-center gap-2">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
              You must map a column to <strong className="mx-1">Account Number (DNO)</strong> to import.
            </div>
          )}

          {/* Data preview table */}
          {analysis.sample_rows.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-700">Preview (first {analysis.sample_rows.length} rows)</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-400">#</th>
                      {analysis.headers.filter(h => mappings[h]).map(h => (
                        <th key={h} className="px-3 py-2 text-left font-medium text-gray-600">
                          {FIELD_LABELS[mappings[h]] || mappings[h]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {analysis.sample_rows.map((row, ri) => (
                      <tr key={ri}>
                        <td className="px-3 py-1.5 text-gray-400">{ri + 1}</td>
                        {analysis.headers.filter(h => mappings[h]).map((h, ci) => {
                          const colIdx = analysis.headers.indexOf(h);
                          return (
                            <td key={ci} className="px-3 py-1.5 text-gray-700 max-w-[200px] truncate">
                              {row[colIdx] ?? ''}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =============================== */}
      {/* Step 4: Results */}
      {/* =============================== */}
      {step === 'done' && importResult && (
        <div className="space-y-6">
          <div className={`rounded-xl border p-6 ${
            importResult.success ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'
          }`}>
            <div className="flex items-start gap-3">
              {importResult.success ? (
                <svg className="w-8 h-8 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/></svg>
              ) : (
                <svg className="w-8 h-8 text-red-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/></svg>
              )}
              <div>
                <h2 className="text-lg font-bold text-gray-900">{importResult.message}</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Tenant: <strong>{importResult.tenant}</strong> | Shop: <strong>{importResult.shop}</strong> | Schema: <code className="text-xs bg-gray-200 px-1 rounded">{importResult.schema}</code>
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              {[
                { label: 'Total Rows', value: importResult.total_rows, color: 'text-gray-800' },
                { label: 'Created', value: importResult.created, color: 'text-green-700' },
                { label: 'Updated', value: importResult.updated, color: 'text-blue-700' },
                { label: 'Skipped', value: importResult.skipped, color: 'text-amber-700' },
              ].map(s => (
                <div key={s.label} className="bg-white rounded-lg p-3 text-center border">
                  <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-xs text-gray-500 mt-1">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Errors */}
          {importResult.errors.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-red-200 overflow-hidden">
              <div className="p-4 border-b border-red-100 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
                <h3 className="text-sm font-semibold text-red-800">Import Errors ({importResult.errors.length})</h3>
              </div>
              <div className="max-h-60 overflow-y-auto p-4 space-y-1">
                {importResult.errors.map((err, i) => (
                  <div key={i} className="text-xs text-red-700 font-mono">{err}</div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-center">
            <button
              onClick={handleReset}
              className="px-6 py-2.5 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition"
            >
              Import Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
