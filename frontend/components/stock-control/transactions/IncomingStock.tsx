'use client';

import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Plus, Trash2, Save, X, Search, PackageCheck, ChevronDown } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface StockItem {
  stock_code: string;
  description: string;
  quantity_on_hand: number;
  supplier_code?: string;
  cost_price: number;
  tax_code: number;
}

interface TaxCode {
  id: number;
  code: string;
  rate: number;
}

interface Supplier {
  id: number;
  name: string;
  supplier_number?: string;
}

interface TransactionLine {
  stock_code: string;
  description: string;
  quantity: number;
  tax_code: number | '';
  unit_cost: number;
  line_total: number;
  vat_amount: number;
}

interface IncomingStockProps {
  onBack: () => void;
}

// ─── Pure helpers ─────────────────────────────────────────────────────────────

function calcLine(
  qty: number,
  cost: number,
  taxRate: number,
  vatType: 'I' | 'E'
): { subtotal: number; vat: number; total: number } {
  const subtotal = qty * cost;
  if (vatType === 'E') {
    const vat = (subtotal * taxRate) / 100;
    return { subtotal, vat, total: subtotal + vat };
  }
  const total = subtotal;
  const vat = (total * taxRate) / (100 + taxRate);
  return { subtotal: total - vat, vat, total };
}

function fmt(n: number) {
  return `R ${n.toFixed(2)}`;
}

// ─── Small UI pieces ──────────────────────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</label>
      {children}
    </div>
  );
}

const inputCls =
  'w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition';

const selectCls =
  'w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition appearance-none cursor-pointer';

// ─── Component ────────────────────────────────────────────────────────────────

export default function IncomingStock({ onBack }: IncomingStockProps) {
  // Header form
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split('T')[0]);
  const [vatType, setVatType] = useState<'I' | 'E'>('E');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [supplierId, setSupplierId] = useState<number | ''>('');
  const [additionalReference, setAdditionalReference] = useState('');
  const [surcharge, setSurcharge] = useState<number | ''>('');

  // Add-line form
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null);
  const [quantity, setQuantity] = useState<number | ''>('');
  const [unitCost, setUnitCost] = useState<number | ''>('');
  const [taxCodeId, setTaxCodeId] = useState<number | ''>('');
  const [showDropdown, setShowDropdown] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Lines
  const [lines, setLines] = useState<TransactionLine[]>([]);

  // Inline edit
  const [editIndex, setEditIndex] = useState<number | null>(null);
  const [editQty, setEditQty] = useState<number | ''>('');
  const [editCost, setEditCost] = useState<number | ''>('');

  const queryClient = useQueryClient();

  // ── Queries ────────────────────────────────────────────────────────────────

  const { data: stockData = [] } = useQuery<StockItem[]>({
    queryKey: ['stock-items'],
    queryFn: async () => {
      const res = await api.get('/api/stock-control/stock-items/');
      return res.data.results ?? res.data;
    },
  });

  const {
    data: suppliersData = [],
    isLoading: suppliersLoading,
    error: suppliersError,
  } = useQuery<Supplier[]>({
    queryKey: ['suppliers'],
    queryFn: async () => {
      const res = await api.get('/api/v1/creditors/creditors/');
      return res.data.results ?? res.data;
    },
  });

  const { data: taxData = [] } = useQuery<TaxCode[]>({
    queryKey: ['tax-codes'],
    queryFn: async () => {
      const res = await api.get('/api/v1/settings/tax-codes/');
      return res.data.results ?? res.data;
    },
  });

  // ── Mutation ───────────────────────────────────────────────────────────────

  const createTransaction = useMutation({
    mutationFn: async (data: object) => {
      const res = await api.post('/api/stock-control/stock-transactions/', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['stock-items'] });
    },
  });

  // ── Close dropdown on outside click ───────────────────────────────────────

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  // ── Derived ────────────────────────────────────────────────────────────────

  const filteredStock =
    searchTerm.length >= 1
      ? stockData
          .filter(
            (item) =>
              item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
              item.description.toLowerCase().includes(searchTerm.toLowerCase())
          )
          .slice(0, 8)
      : [];

  function getTaxRate(id: number | ''): number {
    if (id === '') return 0;
    return taxData.find((t) => t.id === id)?.rate ?? 0;
  }

  // ── Line form handlers ─────────────────────────────────────────────────────

  function handleSelectItem(item: StockItem) {
    setSelectedItem(item);
    setSearchTerm(item.stock_code + ' \u2014 ' + item.description);
    setUnitCost(Number(item.cost_price) || '');
    setTaxCodeId(item.tax_code || '');
    setShowDropdown(false);
  }

  function handleAddLine() {
    const qty = Number(quantity);
    const cost = Number(unitCost);

    // Allow manual typing: try to match search text to a stock item if none selected
    let item = selectedItem;
    if (!item && searchTerm.trim()) {
      const lower = searchTerm.trim().toLowerCase();
      item =
        stockData.find(
          (s) =>
            s.stock_code.toLowerCase() === lower ||
            (s.stock_code + ' \u2014 ' + s.description).toLowerCase() === lower
        ) ?? null;
    }

    if (!item) {
      alert('Please select a stock item from the search list.');
      return;
    }
    if (qty <= 0) {
      alert('Quantity must be greater than 0.');
      return;
    }
    if (cost <= 0) {
      alert('Unit cost must be greater than 0.');
      return;
    }

    const { vat, total } = calcLine(qty, cost, getTaxRate(taxCodeId), vatType);

    setLines((prev) => [
      ...prev,
      {
        stock_code: item!.stock_code,
        description: item!.description,
        quantity: qty,
        tax_code: taxCodeId,
        unit_cost: cost,
        line_total: total,
        vat_amount: vat,
      },
    ]);

    setSelectedItem(null);
    setSearchTerm('');
    setQuantity('');
    setUnitCost('');
    setTaxCodeId('');
  }

  function handleStartEdit(index: number) {
    const line = lines[index];
    setEditIndex(index);
    setEditQty(line.quantity);
    setEditCost(line.unit_cost);
  }

  function handleSaveEdit(index: number) {
    const qty = Number(editQty);
    const cost = Number(editCost);
    if (qty <= 0 || cost <= 0) {
      alert('Quantity and unit cost must be greater than 0.');
      return;
    }
    const line = lines[index];
    const { vat, total } = calcLine(qty, cost, getTaxRate(line.tax_code), vatType);
    setLines((prev) =>
      prev.map((l, i) =>
        i === index ? { ...l, quantity: qty, unit_cost: cost, vat_amount: vat, line_total: total } : l
      )
    );
    setEditIndex(null);
  }

  function handleCancelEdit() {
    setEditIndex(null);
    setEditQty('');
    setEditCost('');
  }

  function handleRemoveLine(index: number) {
    setLines((prev) => prev.filter((_, i) => i !== index));
    if (editIndex === index) setEditIndex(null);
  }

  // ── Totals ─────────────────────────────────────────────────────────────────

  const totals = lines.reduce(
    (acc, l) => ({ qty: acc.qty + l.quantity, vat: acc.vat + l.vat_amount, amount: acc.amount + l.line_total }),
    { qty: 0, vat: 0, amount: 0 }
  );
  const surchargeNum = Number(surcharge) || 0;
  const grandTotal = totals.amount + surchargeNum;

  // ── Submit ─────────────────────────────────────────────────────────────────

  async function handleSubmit() {
    if (!invoiceDate) { alert('Invoice date is required.'); return; }
    if (!invoiceNumber.trim()) { alert('Invoice number is required.'); return; }
    if (lines.length === 0) { alert('Add at least one line item.'); return; }

    try {
      for (const line of lines) {
        // The serializer uses SlugRelatedField(slug_field='stock_code')
        // so stock_item must be the stock_code string.
        // quantity_out must be omitted or 0 — serializer rejects qty_in>0 AND qty_out>0
        // but also rejects sending both, so we only send quantity_in.
        const payload: Record<string, unknown> = {
          transaction_type: 'INCOMING',
          stock_item: line.stock_code,
          quantity_in: line.quantity,
          unit_cost: line.unit_cost,
          unit_price: line.unit_cost,
          value: +(line.quantity * line.unit_cost).toFixed(2),
          discount: 0,
          transaction_date: invoiceDate,
          transaction_number: invoiceNumber.trim(),
        };

        // Only include optional fields when they have a real value
        if (supplierId !== '') payload.supplier = supplierId;
        if (line.tax_code !== '') payload.tax_code = line.tax_code;
        if (additionalReference.trim()) payload.comments = additionalReference.trim();

        await createTransaction.mutateAsync(payload);
      }

      // Reset form
      setInvoiceDate(new Date().toISOString().split('T')[0]);
      setInvoiceNumber('');
      setSupplierId('');
      setAdditionalReference('');
      setSurcharge('');
      setLines([]);
      alert('Incoming stock saved successfully!');
      onBack();
    } catch (error: any) {
      const data = error?.response?.data;
      const msg =
        data?.detail ??
        data?.non_field_errors?.[0] ??
        (data && typeof data === 'object'
          ? Object.entries(data)
              .map(([k, v]: any) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
              .join(' | ')
          : null) ??
        error?.message ??
        'Unknown error occurred';
      alert(`Save failed: ${msg}`);
    }
  }

  // ── Line preview ──────────────────────────────────────────────────────────

  const showPreview = selectedItem && Number(quantity) > 0 && Number(unitCost) > 0;
  const preview = showPreview
    ? calcLine(Number(quantity), Number(unitCost), getTaxRate(taxCodeId), vatType)
    : null;

  const canAdd =
    (!!selectedItem || searchTerm.trim().length > 0) &&
    Number(quantity) > 0 &&
    Number(unitCost) > 0;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&family=DM+Mono:wght@400;500&display=swap');
        .mono { font-family: 'DM Mono', monospace; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
      `}</style>

      {/* Top bar */}
      <div className="sticky top-0 z-20 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-100 transition font-medium"
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <div className="h-4 w-px bg-slate-700" />
        <PackageCheck size={18} className="text-emerald-400" />
        <h1 className="text-sm font-semibold tracking-tight">Incoming Stock</h1>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">

        {/* ── Transaction Details ──────────────────────────────────────────── */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5">
            Transaction Details
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">

            <Field label="Invoice Date *">
              <input type="date" value={invoiceDate}
                onChange={(e) => setInvoiceDate(e.target.value)}
                className={inputCls} />
            </Field>

            <Field label="VAT Option">
              <div className="relative">
                <select value={vatType}
                  onChange={(e) => setVatType(e.target.value as 'I' | 'E')}
                  className={selectCls}>
                  <option value="E">Exclusive of VAT</option>
                  <option value="I">Inclusive of VAT</option>
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </Field>

            <Field label="Invoice Number *">
              <input type="text" value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                placeholder="Supplier's invoice number"
                className={inputCls} />
            </Field>

            <Field label="Supplier">
              {suppliersError && <p className="text-red-400 text-xs mb-1">Failed to load suppliers</p>}
              <div className="relative">
                <select
                  value={String(supplierId)}
                  onChange={(e) => setSupplierId(e.target.value ? parseInt(e.target.value) : '')}
                  className={selectCls}
                  disabled={suppliersLoading}
                >
                  <option value="">{suppliersLoading ? 'Loading...' : '— Select Supplier —'}</option>
                  {suppliersData.map((s) => (
                    <option key={s.id} value={String(s.id)}>
                      {s.supplier_number ? `${s.supplier_number} — ` : ''}{s.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </Field>

            <Field label="Additional Reference">
              <input type="text" value={additionalReference}
                onChange={(e) => setAdditionalReference(e.target.value)}
                placeholder="Notes or PO reference"
                className={inputCls} />
            </Field>

            <Field label="Surcharge (excl. VAT)">
              <input type="number" value={surcharge}
                onChange={(e) => setSurcharge(e.target.value === '' ? '' : parseFloat(e.target.value))}
                step="0.01" min="0" placeholder="0.00"
                className={inputCls} />
            </Field>
          </div>
        </section>

        {/* ── Add Stock Item ───────────────────────────────────────────────── */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5">
            Add Stock Item
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">

            {/* Search */}
            <div ref={searchRef} className="relative">
              <Field label="Stock Code / Description">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setSelectedItem(null);
                      setShowDropdown(true);
                    }}
                    onFocus={() => { if (searchTerm) setShowDropdown(true); }}
                    placeholder="Search stock..."
                    className={`${inputCls} pl-9`}
                  />
                </div>
              </Field>
              {showDropdown && filteredStock.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-30 max-h-52 overflow-y-auto">
                  {filteredStock.map((item) => (
                    <button
                      key={item.stock_code}
                      type="button"
                      onClick={() => handleSelectItem(item)}
                      className="w-full text-left px-4 py-3 hover:bg-slate-700 transition border-b border-slate-700/40 last:border-0"
                    >
                      <p className="text-sm font-medium text-slate-100 mono">{item.stock_code}</p>
                      <p className="text-xs text-slate-400 truncate mt-0.5">{item.description}</p>
                    </button>
                  ))}
                </div>
              )}
              {showDropdown && searchTerm.length >= 1 && filteredStock.length === 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-30 px-4 py-3 text-sm text-slate-500">
                  No items found
                </div>
              )}
            </div>

            <Field label="Quantity">
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value === '' ? '' : parseFloat(e.target.value))}
                step="0.01" min="0" placeholder="0.00"
                className={inputCls}
              />
            </Field>

            <Field label="Unit Cost">
              <input
                type="number"
                value={unitCost}
                onChange={(e) => setUnitCost(e.target.value === '' ? '' : parseFloat(e.target.value))}
                step="0.01" min="0" placeholder="0.00"
                className={inputCls}
              />
            </Field>

            <Field label="Tax Code">
              <div className="relative">
                <select
                  value={taxCodeId}
                  onChange={(e) => setTaxCodeId(e.target.value ? parseInt(e.target.value) : '')}
                  className={selectCls}
                >
                  <option value="">— Tax Code —</option>
                  {taxData.map((t) => (
                    <option key={t.id} value={t.id}>{t.code} ({t.rate}%)</option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </Field>
          </div>

          {/* Live preview */}
          {preview && (
            <div className="mb-4 flex items-center gap-6 px-4 py-3 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-400">
              <span>Subtotal: <strong className="text-slate-200 mono">{fmt(preview.subtotal)}</strong></span>
              <span>VAT: <strong className="text-slate-200 mono">{fmt(preview.vat)}</strong></span>
              <span>Total: <strong className="text-emerald-400 mono">{fmt(preview.total)}</strong></span>
            </div>
          )}

          <button
            onClick={handleAddLine}
            disabled={!canAdd}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition"
          >
            <Plus size={16} />
            Add Line Item
          </button>
        </section>

        {/* ── Goods Received Note ──────────────────────────────────────────── */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
              Goods Received Note
            </p>
            <span className="mono text-xs text-slate-500">{lines.length} line{lines.length !== 1 ? 's' : ''}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  {['Stock Code', 'Description', 'Qty', 'Unit Cost', 'VAT', 'Total', ''].map((h, i) => (
                    <th
                      key={i}
                      className={`px-4 py-3 text-xs font-semibold uppercase tracking-widest text-slate-500 ${
                        i === 0 ? 'text-left pl-6' : i >= 2 && i <= 5 ? 'text-right' : i === 1 ? 'text-left' : ''
                      }`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lines.length === 0 && (
                  <tr>
                    <td colSpan={7} className="text-center py-14 text-slate-600 text-sm">
                      No items added yet — use the form above.
                    </td>
                  </tr>
                )}
                {lines.map((line, i) => (
                  <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition group">
                    <td className="pl-6 pr-4 py-3 mono text-emerald-400 font-medium text-sm">{line.stock_code}</td>
                    <td className="px-4 py-3 text-slate-300 max-w-xs truncate">{line.description}</td>
                    <td className="px-4 py-3 text-right">
                      {editIndex === i ? (
                        <input type="number" value={editQty}
                          onChange={(e) => setEditQty(e.target.value === '' ? '' : parseFloat(e.target.value))}
                          step="0.01" min="0"
                          className="w-20 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-right text-slate-100 focus:outline-none focus:border-emerald-500 mono text-sm"
                        />
                      ) : (
                        <span className="mono">{line.quantity.toFixed(2)}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {editIndex === i ? (
                        <input type="number" value={editCost}
                          onChange={(e) => setEditCost(e.target.value === '' ? '' : parseFloat(e.target.value))}
                          step="0.01" min="0"
                          className="w-24 px-2 py-1 bg-slate-700 border border-slate-600 rounded text-right text-slate-100 focus:outline-none focus:border-emerald-500 mono text-sm"
                        />
                      ) : (
                        <span className="mono">{fmt(line.unit_cost)}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right mono text-slate-400">{fmt(line.vat_amount)}</td>
                    <td className="px-4 py-3 text-right mono font-semibold text-slate-100">{fmt(line.line_total)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 justify-end">
                        {editIndex === i ? (
                          <>
                            <button onClick={() => handleSaveEdit(i)}
                              className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded transition">
                              <Save size={12} /> Save
                            </button>
                            <button onClick={handleCancelEdit}
                              className="p-1.5 text-slate-400 hover:text-slate-200 bg-slate-700 hover:bg-slate-600 rounded transition">
                              <X size={12} />
                            </button>
                          </>
                        ) : (
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                            <button onClick={() => handleStartEdit(i)}
                              className="px-2.5 py-1 text-xs font-semibold text-slate-300 hover:text-white bg-slate-700 hover:bg-slate-600 rounded transition">
                              Edit
                            </button>
                            <button onClick={() => handleRemoveLine(i)}
                              className="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition">
                              <Trash2 size={13} />
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals */}
          {lines.length > 0 && (
            <div className="border-t border-slate-800 px-6 py-5 flex justify-end">
              <div className="w-64 space-y-2.5">
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Total Quantity</span>
                  <span className="mono font-medium text-slate-200">{totals.qty.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm text-slate-400">
                  <span>Total VAT</span>
                  <span className="mono font-medium text-slate-200">{fmt(totals.vat)}</span>
                </div>
                {surchargeNum > 0 && (
                  <div className="flex justify-between text-sm text-slate-400">
                    <span>Surcharge</span>
                    <span className="mono font-medium text-slate-200">{fmt(surchargeNum)}</span>
                  </div>
                )}
                <div className="flex justify-between text-base font-bold border-t border-slate-700 pt-3 text-slate-100">
                  <span>Grand Total</span>
                  <span className="mono text-emerald-400">{fmt(grandTotal)}</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* ── Actions ──────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-end gap-3 pb-10">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg transition"
          >
            <X size={16} />
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={createTransaction.isPending || lines.length === 0 || !invoiceNumber.trim()}
            className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition"
          >
            <Save size={16} />
            {createTransaction.isPending ? 'Saving...' : 'Save & Update Stock'}
          </button>
        </div>

      </div>
    </div>
  );
}