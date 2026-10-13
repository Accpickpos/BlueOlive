'use client';

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import type { TenderReconciliationRecord, TenderReconciliationSummaryRow } from '@/lib/posApi';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertCircle, Loader2, Search } from 'lucide-react';

const TENDER_TYPE_LABELS: Record<string, string> = {
  CHEQUE: 'Cheque',
  VOUCHER: 'Voucher',
  SPEEDPOINT: 'Speedpoint/Card',
  EFT: 'EFT',
};

const STATUS_CLASSES: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  RECONCILED: 'bg-green-100 text-green-800',
  VARIANCE: 'bg-red-100 text-red-800',
};

const todayISO = () => new Date().toISOString().split('T')[0];

const groupKey = (row: TenderReconciliationSummaryRow) =>
  `${row.sale_date}|${row.station_number}|${row.tender_type}|${row.reconciliation_status}`;

export default function CardReconciliationPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);

  const [dateFrom, setDateFrom] = useState(todayISO());
  const [dateTo, setDateTo] = useState(todayISO());
  const [stationNumber, setStationNumber] = useState('');

  const [summaryRows, setSummaryRows] = useState<TenderReconciliationSummaryRow[]>([]);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [activeGroup, setActiveGroup] = useState<TenderReconciliationSummaryRow | null>(null);
  const [tenders, setTenders] = useState<TenderReconciliationRecord[]>([]);
  const [tendersLoading, setTendersLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());
  const [rowBusyId, setRowBusyId] = useState<string | number | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);

  const runSummarySearch = async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const rows = await posAPIRef.current.getTenderReconciliationSummary({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        station_number: stationNumber || undefined,
      });
      setSummaryRows(rows);
    } catch (error) {
      console.error('Error fetching reconciliation summary:', error);
      setSummaryError('Failed to load the reconciliation summary.');
      setSummaryRows([]);
    } finally {
      setSummaryLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading || !user) return;
    runSummarySearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const openGroup = async (row: TenderReconciliationSummaryRow) => {
    setActiveGroup(row);
    setSelectedIds(new Set());
    setTendersLoading(true);
    try {
      const response = await posAPIRef.current.listTenders({
        tender_type: row.tender_type,
      });
      const all = Array.isArray(response) ? response : response.results;
      const filtered = all.filter(
        (t) =>
          t.sale_date === row.sale_date &&
          String(t.station_number) === String(row.station_number) &&
          t.reconciliation_status === row.reconciliation_status
      );
      setTenders(filtered);
    } catch (error) {
      console.error('Error loading tenders for group:', error);
      setTenders([]);
    } finally {
      setTendersLoading(false);
    }
  };

  const refreshActiveGroup = () => {
    if (activeGroup) openGroup(activeGroup);
    runSummarySearch();
  };

  const toggleSelected = (id: string | number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleReconcile = async (tender: TenderReconciliationRecord) => {
    setRowBusyId(tender.id);
    try {
      await posAPIRef.current.reconcileTender(tender.id, 'RECONCILED');
      refreshActiveGroup();
    } catch (error) {
      console.error('Error reconciling tender:', error);
      alert('Failed to mark this tender as reconciled.');
    } finally {
      setRowBusyId(null);
    }
  };

  const handleFlagVariance = async (tender: TenderReconciliationRecord) => {
    const note = window.prompt(
      `Why does this ${TENDER_TYPE_LABELS[tender.tender_type] || tender.tender_type} tender (R${Number(tender.amount).toFixed(2)}) not match the card machine? (required)`
    );
    if (!note) return;
    setRowBusyId(tender.id);
    try {
      await posAPIRef.current.reconcileTender(tender.id, 'VARIANCE', note);
      refreshActiveGroup();
    } catch (error) {
      console.error('Error flagging variance:', error);
      alert('Failed to flag this tender as a variance.');
    } finally {
      setRowBusyId(null);
    }
  };

  const handleBulkReconcile = async () => {
    if (selectedIds.size === 0) return;
    setBulkBusy(true);
    try {
      await posAPIRef.current.bulkReconcileTenders(Array.from(selectedIds));
      refreshActiveGroup();
    } catch (error) {
      console.error('Error bulk reconciling tenders:', error);
      alert('Failed to mark the selected tenders as reconciled.');
    } finally {
      setBulkBusy(false);
    }
  };

  const selectableIds = tenders
    .filter((t) => t.reconciliation_status !== 'RECONCILED')
    .map((t) => t.id);
  const allSelectableSelected =
    selectableIds.length > 0 && selectableIds.every((id) => selectedIds.has(id));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Card Tender Reconciliation</h1>
        <p className="text-sm text-gray-500">
          Compare card/cheque/EFT tenders captured at the till against your card machine&apos;s own
          settlement report, and mark them reconciled or flag a variance.
        </p>
      </div>

      <div className="p-6 pb-0">
        <Card>
          <CardContent className="pt-6 space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setActiveGroup(null);
                runSummarySearch();
              }}
              className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end"
            >
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">From</label>
                <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">To</label>
                <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Station</label>
                <Input
                  placeholder="All stations"
                  value={stationNumber}
                  onChange={(e) => setStationNumber(e.target.value)}
                />
              </div>
              <div>
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={summaryLoading}>
                  {summaryLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                  Search
                </Button>
              </div>
            </form>

            {summaryError && (
              <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                <AlertCircle className="w-4 h-4" />
                {summaryError}
              </div>
            )}

            <div className="overflow-x-auto border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Station</TableHead>
                    <TableHead>Tender Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Count</TableHead>
                    <TableHead className="text-right">Total Amount</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summaryLoading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : summaryRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        No card/cheque/EFT tenders found for this date range.
                      </TableCell>
                    </TableRow>
                  ) : (
                    summaryRows.map((row) => (
                      <TableRow key={groupKey(row)}>
                        <TableCell>{row.sale_date}</TableCell>
                        <TableCell>{row.station_number}</TableCell>
                        <TableCell>{TENDER_TYPE_LABELS[row.tender_type] || row.tender_type}</TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLASSES[row.reconciliation_status] || 'bg-gray-100 text-gray-800'}`}
                          >
                            {row.reconciliation_status}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">{row.count}</TableCell>
                        <TableCell className="text-right">R{Number(row.total_amount).toFixed(2)}</TableCell>
                        <TableCell className="text-right">
                          <button
                            onClick={() => openGroup(row)}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                          >
                            View
                          </button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {activeGroup && (
        <div className="p-6">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {TENDER_TYPE_LABELS[activeGroup.tender_type] || activeGroup.tender_type} tenders —{' '}
                    {activeGroup.sale_date}, station {activeGroup.station_number}
                  </h2>
                  <p className="text-sm text-gray-500">
                    Compare each authorization code against your card machine&apos;s settlement slip.
                  </p>
                </div>
                <Button
                  onClick={handleBulkReconcile}
                  disabled={selectedIds.size === 0 || bulkBusy}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {bulkBusy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Mark selected reconciled ({selectedIds.size})
                </Button>
              </div>

              <div className="overflow-x-auto border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <input
                          type="checkbox"
                          checked={allSelectableSelected}
                          onChange={(e) =>
                            setSelectedIds(e.target.checked ? new Set(selectableIds) : new Set())
                          }
                        />
                      </TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Card Type</TableHead>
                      <TableHead>Authorization Code</TableHead>
                      <TableHead>Cashier</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Note</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tendersLoading ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                          Loading tenders...
                        </TableCell>
                      </TableRow>
                    ) : tenders.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                          No tenders in this group.
                        </TableCell>
                      </TableRow>
                    ) : (
                      tenders.map((t) => {
                        const busy = rowBusyId === t.id;
                        const reconciled = t.reconciliation_status === 'RECONCILED';
                        return (
                          <TableRow key={t.id}>
                            <TableCell>
                              <input
                                type="checkbox"
                                disabled={reconciled}
                                checked={selectedIds.has(t.id)}
                                onChange={() => toggleSelected(t.id)}
                              />
                            </TableCell>
                            <TableCell>R{Number(t.amount).toFixed(2)}</TableCell>
                            <TableCell>{t.card_type || '-'}</TableCell>
                            <TableCell>{t.authorization_code || '-'}</TableCell>
                            <TableCell>{t.cashier_username || '-'}</TableCell>
                            <TableCell>
                              <span
                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLASSES[t.reconciliation_status] || 'bg-gray-100 text-gray-800'}`}
                              >
                                {t.reconciliation_status}
                              </span>
                            </TableCell>
                            <TableCell className="max-w-xs truncate">{t.reconciliation_note || '-'}</TableCell>
                            <TableCell className="text-right">
                              {!reconciled && (
                                <div className="flex justify-end gap-3">
                                  <button
                                    onClick={() => handleReconcile(t)}
                                    disabled={busy}
                                    className="text-green-600 hover:text-green-700 text-sm font-medium disabled:opacity-50"
                                  >
                                    {busy ? 'Saving...' : 'Reconcile'}
                                  </button>
                                  <button
                                    onClick={() => handleFlagVariance(t)}
                                    disabled={busy}
                                    className="text-red-600 hover:text-red-700 text-sm font-medium disabled:opacity-50"
                                  >
                                    Flag Variance
                                  </button>
                                </div>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
