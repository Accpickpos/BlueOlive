'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
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
import { PlusCircle, Search, AlertCircle, Loader2, Eye, Printer, Mail } from 'lucide-react';
import type { TransactionQueryType, POSTransactionAPI } from '@/lib/posApi';
import {
  printCashSale, emailCashSale,
  printCreditNote, emailCreditNote,
  printLaybye, emailLaybye,
  printQuotation, emailQuotation,
  printJobCard, emailJobCard,
  printRepair, emailRepair,
  printPayout, emailPayout,
  printInvoice, emailInvoice,
  printReceipt, emailReceipt,
} from '@/lib/printUtils';

// Per-type wiring for the "View/Print/Email" row actions on search results:
// getFn fetches the full record (search results only carry a slim summary),
// viewPath (when present) links to that type's own detail page instead of
// just opening a print preview.
const TX_ACTIONS: Record<
  TransactionQueryType,
  {
    getFn: (api: POSTransactionAPI, id: string | number) => Promise<any>;
    printFn: (doc: any, isReprint?: boolean) => Promise<void>;
    emailFn: (doc: any, email: string, isReprint?: boolean) => Promise<{ success: boolean; message: string }>;
    viewPath?: (id: string | number) => string;
  }
> = {
  CASH_SALE: { getFn: (api, id) => api.getCashSale(id), printFn: printCashSale, emailFn: emailCashSale, viewPath: (id) => `/dashboard/pos/cash-sales/${id}` },
  INVOICE: { getFn: (api, id) => api.getInvoice(id), printFn: printInvoice, emailFn: emailInvoice, viewPath: (id) => `/dashboard/pos/invoices/${id}` },
  RECEIPT: { getFn: (api, id) => api.getReceipt(id), printFn: printReceipt, emailFn: emailReceipt },
  CREDIT_NOTE: { getFn: (api, id) => api.getCreditNote(id), printFn: printCreditNote, emailFn: emailCreditNote },
  LAYBYE: { getFn: (api, id) => api.getLaybye(id), printFn: printLaybye, emailFn: emailLaybye, viewPath: (id) => `/dashboard/pos/laybays/${id}` },
  QUOTATION: { getFn: (api, id) => api.getQuotation(id), printFn: printQuotation, emailFn: emailQuotation, viewPath: (id) => `/dashboard/pos/quotes/${id}` },
  JOB_CARD: { getFn: (api, id) => api.getJobCard(id), printFn: printJobCard, emailFn: emailJobCard },
  REPAIR: { getFn: (api, id) => api.getRepairControl(id), printFn: printRepair, emailFn: emailRepair },
  PAYOUT: { getFn: (api, id) => api.getPayout(id), printFn: printPayout, emailFn: emailPayout },
};

const TYPE_LABELS: Record<string, string> = {
  CASH_SALE: 'Cash Sale',
  INVOICE: 'Invoice',
  RECEIPT: 'Receipt on Account',
  CREDIT_NOTE: 'Credit Note',
  LAYBYE: 'Laybye',
  QUOTATION: 'Quotation',
  JOB_CARD: 'Job Card',
  REPAIR: 'Repair',
  PAYOUT: 'Payout',
};

const ALL_TRANSACTION_TYPES = Object.keys(TYPE_LABELS) as TransactionQueryType[];

interface TransactionResult {
  id: number | string;
  transaction_type: TransactionQueryType;
  number: string | null;
  date: string | null;
  party_name: string | null;
  total_amount: number | null;
  status: string | null;
}

const todayISO = () => new Date().toISOString().split('T')[0];

const STATUS_CLASSES: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  RESOLVED: 'bg-green-100 text-green-800',
  CLOSED: 'bg-gray-100 text-gray-800',
};

export default function TransactionQueryPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);
  const [rowActionKey, setRowActionKey] = useState<string | null>(null);

  const [queries, setQueries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  // Transaction search — browses actual transactions (cash sales, invoices,
  // laybyes, etc.) via TransactionQueryViewSet.search, separate from the
  // logged-complaint-tickets list below.
  const [txType, setTxType] = useState<'ALL' | (typeof ALL_TRANSACTION_TYPES)[number]>('ALL');
  const [txNumber, setTxNumber] = useState('');
  const [txCustomer, setTxCustomer] = useState('');
  const [txDateFrom, setTxDateFrom] = useState(todayISO());
  const [txDateTo, setTxDateTo] = useState(todayISO());
  const [txResults, setTxResults] = useState<TransactionResult[]>([]);
  const [txLoading, setTxLoading] = useState(false);
  const [txError, setTxError] = useState<string | null>(null);
  const [txSearched, setTxSearched] = useState(false);

  const runTransactionSearch = async () => {
    setTxLoading(true);
    setTxError(null);
    try {
      const typesToSearch = txType === 'ALL' ? ALL_TRANSACTION_TYPES : [txType];
      const responses = await Promise.all(
        typesToSearch.map((type) =>
          posAPIRef.current.searchTransactionQueries({
            query_type: type,
            transaction_number: txNumber || undefined,
            customer_name: txCustomer || undefined,
            date_from: txDateFrom || undefined,
            date_to: txDateTo || undefined,
          }).catch((err) => {
            console.error(`Transaction search failed for ${type}:`, err);
            return { query_type: type, results_count: 0, results: [] };
          })
        )
      );

      const merged: TransactionResult[] = responses.flatMap((r) =>
        (r.results || []).map((row: any) => ({ ...row, transaction_type: r.query_type }))
      );
      merged.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));

      setTxResults(merged);
      setTxSearched(true);
    } catch (error) {
      console.error('Error searching transactions:', error);
      setTxError('Failed to search transactions');
    } finally {
      setTxLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading || !user) return;
    // Land on the page already showing today's transactions.
    runTransactionSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const rowKey = (r: TransactionResult) => `${r.transaction_type}-${r.id}`;

  const handleView = (r: TransactionResult) => {
    const actions = TX_ACTIONS[r.transaction_type];
    if (actions.viewPath) {
      router.push(actions.viewPath(r.id));
    } else {
      // No detail page for this type — fall back to a plain preview
      // (isReprint=false: manual §1 "6. Transaction Query" only requires
      // the COPY watermark on an actual reprint, not on "Display").
      handlePrint(r, false);
    }
  };

  // isReprint defaults true here: anything printed/emailed from Transaction
  // Query IS a reprint per manual §1 "6. Transaction Query" ("The reprint
  // will display the word COPY"). handleView passes false for its
  // view-only fallback above.
  const handlePrint = async (r: TransactionResult, isReprint: boolean = true) => {
    const actions = TX_ACTIONS[r.transaction_type];
    const key = rowKey(r);
    setRowActionKey(key);
    try {
      const doc = await actions.getFn(posAPIRef.current, r.id);
      await actions.printFn(doc, isReprint);
    } catch (error) {
      console.error(`Failed to print ${r.transaction_type} ${r.number}:`, error);
      alert('Failed to load this transaction for printing.');
    } finally {
      setRowActionKey(null);
    }
  };

  const handleEmail = async (r: TransactionResult) => {
    const email = window.prompt(`Email address to send ${TYPE_LABELS[r.transaction_type]} ${r.number || ''} to:`);
    if (!email) return;

    const actions = TX_ACTIONS[r.transaction_type];
    const key = rowKey(r);
    setRowActionKey(key);
    try {
      const doc = await actions.getFn(posAPIRef.current, r.id);
      const result = await actions.emailFn(doc, email, true);
      alert(result.message);
    } catch (error) {
      console.error(`Failed to email ${r.transaction_type} ${r.number}:`, error);
      alert('Failed to load this transaction for emailing.');
    } finally {
      setRowActionKey(null);
    }
  };

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchQueries = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listTransactionQueries({
          query_status: statusFilter === 'all' ? undefined : (statusFilter as any),
          page: currentPage,
        });
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setQueries(
          raw.map((q: any) => ({
            id: q.id,
            query_number: q.query_number ?? '',
            query_date: q.query_date ?? '',
            transaction_type: q.transaction_type_display ?? TYPE_LABELS[q.transaction_type] ?? q.transaction_type,
            transaction_number: q.transaction_number ?? '',
            customer_name: q.customer_name ?? '',
            query_description: q.query_description ?? '',
            query_status: q.query_status ?? 'OPEN',
            assigned_to_name: q.assigned_to_name ?? '',
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching transaction queries:', error);
          setQueries([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchQueries();
    return () => { cancelled = true; };
  }, [user, authLoading, statusFilter, currentPage]);

  const filteredQueries = queries.filter((q) =>
    !searchTerm ||
    q.query_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.transaction_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleResolve = async (id: number) => {
    const notes = window.prompt('Resolution notes:');
    if (notes === null) return;
    setResolvingId(id);
    try {
      await posAPIRef.current.resolveTransactionQuery(id, notes);
      setQueries((prev) => prev.map((q) => (q.id === id ? { ...q, query_status: 'RESOLVED' } : q)));
    } catch (error) {
      console.error('Error resolving query:', error);
    } finally {
      setResolvingId(null);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transaction Query</h1>
            <p className="text-sm text-gray-500">Log and resolve customer queries about past transactions</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard/pos/transaction-query/create"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              <PlusCircle className="w-4 h-4" />
              New Query
            </Link>
          </div>
        </div>
      </div>

      {/* Transaction Search — browse actual transactions by number/customer/date */}
      <div className="p-6 pb-0">
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Search Transactions</h2>
              <p className="text-sm text-gray-500">
                Defaults to today. Search across cash sales, invoices, receipts, credit notes, laybyes,
                quotations, job cards, repairs and payouts.
              </p>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                runTransactionSearch();
              }}
              className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end"
            >
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                <select
                  value={txType}
                  onChange={(e) => setTxType(e.target.value as any)}
                  className="w-full px-3 py-2 border rounded-lg bg-white text-sm"
                >
                  <option value="ALL">All Types</option>
                  {ALL_TRANSACTION_TYPES.map((t) => (
                    <option key={t} value={t}>{TYPE_LABELS[t]}</option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">Transaction #</label>
                <Input
                  placeholder="e.g. INV-..."
                  value={txNumber}
                  onChange={(e) => setTxNumber(e.target.value)}
                />
              </div>
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">Customer</label>
                <Input
                  placeholder="Customer name"
                  value={txCustomer}
                  onChange={(e) => setTxCustomer(e.target.value)}
                />
              </div>
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">From</label>
                <Input type="date" value={txDateFrom} onChange={(e) => setTxDateFrom(e.target.value)} />
              </div>
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-gray-600 mb-1">To</label>
                <Input type="date" value={txDateTo} onChange={(e) => setTxDateTo(e.target.value)} />
              </div>
              <div className="md:col-span-1">
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={txLoading}>
                  {txLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
                  Search
                </Button>
              </div>
            </form>

            {txError && (
              <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">
                <AlertCircle className="w-4 h-4" />
                {txError}
              </div>
            )}

            <div className="overflow-x-auto border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Number</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {txLoading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        Searching...
                      </TableCell>
                    </TableRow>
                  ) : txResults.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        {txSearched ? 'No transactions found for this search' : 'Search to see transactions'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    txResults.map((r, idx) => {
                      const busy = rowActionKey === rowKey(r);
                      return (
                        <TableRow key={`${rowKey(r)}-${idx}`}>
                          <TableCell>{TYPE_LABELS[r.transaction_type] || r.transaction_type}</TableCell>
                          <TableCell className="font-medium">{r.number ?? '-'}</TableCell>
                          <TableCell>{r.date ?? '-'}</TableCell>
                          <TableCell>{r.party_name ?? '-'}</TableCell>
                          <TableCell className="text-right">
                            {r.total_amount !== null && r.total_amount !== undefined
                              ? `R${Number(r.total_amount).toFixed(2)}`
                              : '-'}
                          </TableCell>
                          <TableCell>{r.status ?? '-'}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <button
                                onClick={() => handleView(r)}
                                disabled={busy}
                                title="View"
                                className="p-1.5 rounded-md text-gray-500 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-50"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handlePrint(r)}
                                disabled={busy}
                                title="Print"
                                className="p-1.5 rounded-md text-gray-500 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-50"
                              >
                                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Printer className="w-4 h-4" />}
                              </button>
                              <button
                                onClick={() => handleEmail(r)}
                                disabled={busy}
                                title="Email"
                                className="p-1.5 rounded-md text-gray-500 hover:text-blue-600 hover:bg-blue-50 disabled:opacity-50"
                              >
                                <Mail className="w-4 h-4" />
                              </button>
                            </div>
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

      {/* Logged Queries */}
      <div className="px-6 pt-6">
        <h2 className="text-lg font-semibold text-gray-900">Logged Queries</h2>
        <p className="text-sm text-gray-500 mb-2">Customer complaints or questions raised about a specific transaction.</p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-b px-6 py-4">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by query number, transaction number or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border rounded-lg bg-white font-medium"
          >
            <option value="all">All Status</option>
            <option value="OPEN">Open</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
          <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
            Search
          </Button>
        </form>
      </div>

      {/* Queries Table */}
      <div className="p-6">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading queries...</p>
          </div>
        ) : filteredQueries.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No transaction queries found</p>
                <Link href="/dashboard/pos/transaction-query/create">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Log First Query
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query #</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Transaction #</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Assigned To</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredQueries.map((q) => (
                    <TableRow key={q.id}>
                      <TableCell className="font-medium">{q.query_number}</TableCell>
                      <TableCell>{q.transaction_type}</TableCell>
                      <TableCell>{q.transaction_number}</TableCell>
                      <TableCell>{q.customer_name || '-'}</TableCell>
                      <TableCell className="max-w-xs truncate">{q.query_description}</TableCell>
                      <TableCell>{q.assigned_to_name || '-'}</TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${STATUS_CLASSES[q.query_status] || 'bg-gray-100 text-gray-800'}`}>
                          {q.query_status.replace('_', ' ')}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {q.query_status !== 'RESOLVED' && q.query_status !== 'CLOSED' && (
                          <button
                            onClick={() => handleResolve(q.id)}
                            disabled={resolvingId === q.id}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-50"
                          >
                            {resolvingId === q.id ? 'Resolving...' : 'Resolve'}
                          </button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {filteredQueries.length > 0 && (
        <div className="flex justify-between items-center px-6 py-4 bg-white border-t">
          <p className="text-sm text-gray-600">Page {currentPage}</p>
          <div className="flex gap-2">
            <Button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              variant="outline"
            >
              Previous
            </Button>
            <Button
              onClick={() => setCurrentPage(currentPage + 1)}
              variant="outline"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
