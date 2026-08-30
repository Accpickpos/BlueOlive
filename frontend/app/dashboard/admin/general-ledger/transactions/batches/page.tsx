'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glBatchesApi } from '@/lib/general-ledger';
import { GLBatch, GLBatchCreateData } from '@/lib/types/generalLedger';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
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
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Loader2, Plus, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

const today = () => new Date().toISOString().slice(0, 10);

function emptyLine(batchno: number): GLBatchCreateData {
  return {
    accno: 0,
    batchno,
    capturedat: today(),
    date: today(),
    drorcr: 'D',
    amount: 0,
    reference: '',
    details: '',
    period: 1,
  };
}

export default function GLBatchesPage() {
  const queryClient = useQueryClient();
  const [selectedBatchno, setSelectedBatchno] = useState<number | null>(null);
  const [newBatchno, setNewBatchno] = useState('');
  const [lineForm, setLineForm] = useState<GLBatchCreateData>(emptyLine(0));
  const [error, setError] = useState<string | null>(null);

  const { data: allBatches, isLoading: listLoading } = useQuery({
    queryKey: ['gl-batches-all'],
    queryFn: () => glBatchesApi.list({ ordering: '-capturedat', page_size: 500 }),
  });

  const unpostedGroups = useMemo(() => {
    const rows = allBatches?.results || [];
    const groups = new Map<number, { count: number; total: number; hasPosted: boolean }>();
    rows.forEach((row) => {
      const g = groups.get(row.batchno) || { count: 0, total: 0, hasPosted: false };
      g.count += 1;
      g.total += row.drorcr === 'D' ? row.amount : -row.amount;
      if (row.postdate) g.hasPosted = true;
      groups.set(row.batchno, g);
    });
    return Array.from(groups.entries())
      .filter(([, g]) => !g.hasPosted)
      .sort((a, b) => b[0] - a[0]);
  }, [allBatches]);

  const { data: linesForSelected, isLoading: linesLoading } = useQuery({
    queryKey: ['gl-batch-lines', selectedBatchno],
    queryFn: () => glBatchesApi.list({ batchno: selectedBatchno }),
    enabled: selectedBatchno !== null,
  });

  const { data: balanceCheck } = useQuery({
    queryKey: ['gl-batch-balance', selectedBatchno],
    queryFn: () => glBatchesApi.balanceCheck(selectedBatchno as number),
    enabled: selectedBatchno !== null,
  });

  const addLineMutation = useMutation({
    mutationFn: (body: GLBatchCreateData) => glBatchesApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-batch-lines', selectedBatchno] });
      queryClient.invalidateQueries({ queryKey: ['gl-batch-balance', selectedBatchno] });
      queryClient.invalidateQueries({ queryKey: ['gl-batches-all'] });
      setLineForm(emptyLine(selectedBatchno || 0));
      setError(null);
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to add line')),
  });

  const deleteLineMutation = useMutation({
    mutationFn: (id: number) => glBatchesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-batch-lines', selectedBatchno] });
      queryClient.invalidateQueries({ queryKey: ['gl-batch-balance', selectedBatchno] });
      queryClient.invalidateQueries({ queryKey: ['gl-batches-all'] });
    },
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to delete line')),
  });

  const postMutation = useMutation({
    mutationFn: (batchno: number) => glBatchesApi.post(batchno),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['gl-batches-all'] });
      queryClient.invalidateQueries({ queryKey: ['gl-batch-lines', selectedBatchno] });
      queryClient.invalidateQueries({ queryKey: ['gl-batch-balance', selectedBatchno] });
      window.alert(`Posted ${result.lines_posted} lines to GL batch ${result.gl_batchno}.`);
      setSelectedBatchno(null);
    },
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to post batch')),
  });

  const startNewBatch = () => {
    const n = parseInt(newBatchno);
    if (!n) {
      setError('Enter a batch number to start capturing.');
      return;
    }
    setSelectedBatchno(n);
    setLineForm(emptyLine(n));
    setError(null);
  };

  const lines = linesForSelected?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/transactions">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Journal Batches</h1>
          <p className="text-gray-600 mt-1">Capture, balance-check, and post journal batches</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 md:col-span-1">
          <h2 className="text-lg font-bold mb-4">Unposted Batches</h2>

          <div className="flex gap-2 mb-4">
            <Input
              type="number"
              placeholder="New batch #"
              value={newBatchno}
              onChange={(e) => setNewBatchno(e.target.value)}
            />
            <Button size="sm" onClick={startNewBatch}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {listLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : unpostedGroups.length === 0 ? (
            <p className="text-sm text-gray-500">No unposted batches.</p>
          ) : (
            <div className="space-y-1">
              {unpostedGroups.map(([batchno, g]) => (
                <button
                  key={batchno}
                  onClick={() => setSelectedBatchno(batchno)}
                  className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center ${
                    selectedBatchno === batchno ? 'bg-blue-50 border border-blue-300' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <span>
                    Batch {batchno} <span className="text-gray-400">({g.count} lines)</span>
                  </span>
                  <span className={g.total === 0 ? 'text-green-600' : 'text-amber-600'}>
                    {g.total === 0 ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                  </span>
                </button>
              ))}
            </div>
          )}
        </Card>

        <div className="md:col-span-2 space-y-4">
          {selectedBatchno === null ? (
            <Card className="p-6 text-center text-gray-500">
              Select an existing batch or start a new one.
            </Card>
          ) : (
            <>
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold">Batch {selectedBatchno}</h2>
                  {balanceCheck && 'is_balanced' in balanceCheck && (
                    <Badge variant={balanceCheck.is_balanced ? 'default' : 'destructive'}>
                      {balanceCheck.is_balanced ? 'Balanced' : 'Unbalanced'}
                    </Badge>
                  )}
                </div>

                {balanceCheck && 'total_debit' in balanceCheck && (
                  <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                    <div>
                      <p className="text-gray-500">Total Debit</p>
                      <p className="font-bold">{balanceCheck.total_debit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Total Credit</p>
                      <p className="font-bold">{balanceCheck.total_credit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Lines</p>
                      <p className="font-bold">{balanceCheck.line_count ?? lines.length}</p>
                    </div>
                  </div>
                )}

                {linesLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : lines.length === 0 ? (
                  <p className="text-sm text-gray-500 mb-4">No lines captured yet.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account</TableHead>
                        <TableHead>Dr/Cr</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Reference</TableHead>
                        <TableHead>Details</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lines.map((line: GLBatch) => (
                        <TableRow key={line.id}>
                          <TableCell>{line.accno}</TableCell>
                          <TableCell>{line.drorcr_display}</TableCell>
                          <TableCell className="text-right">
                            {line.amount.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell>{line.reference}</TableCell>
                          <TableCell>{line.details}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600"
                              onClick={() => deleteLineMutation.mutate(line.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}

                <div className="mt-4 flex justify-end">
                  <Button
                    onClick={() => postMutation.mutate(selectedBatchno)}
                    disabled={postMutation.isPending || lines.length === 0 || !balanceCheck?.is_balanced}
                  >
                    {postMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Post Batch to Ledger
                  </Button>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="font-bold mb-4">Add Line</h3>
                {error && (
                  <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2 mb-4">
                    {error}
                  </div>
                )}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm font-medium">Account</label>
                    <Input
                      type="number"
                      value={lineForm.accno || ''}
                      onChange={(e) => setLineForm({ ...lineForm, accno: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Dr/Cr</label>
                    <select
                      value={lineForm.drorcr}
                      onChange={(e) => setLineForm({ ...lineForm, drorcr: e.target.value as 'D' | 'C' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="D">Debit</option>
                      <option value="C">Credit</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Amount</label>
                    <Input
                      type="number"
                      step="0.01"
                      value={lineForm.amount || ''}
                      onChange={(e) => setLineForm({ ...lineForm, amount: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Period</label>
                    <Input
                      type="number"
                      min={1}
                      max={13}
                      value={lineForm.period}
                      onChange={(e) => setLineForm({ ...lineForm, period: parseInt(e.target.value) || 1 })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Date</label>
                    <Input
                      type="date"
                      value={lineForm.date}
                      onChange={(e) => setLineForm({ ...lineForm, date: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Reference</label>
                    <Input
                      value={lineForm.reference}
                      maxLength={10}
                      onChange={(e) => setLineForm({ ...lineForm, reference: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="text-sm font-medium">Details</label>
                    <Input
                      value={lineForm.details}
                      maxLength={30}
                      onChange={(e) => setLineForm({ ...lineForm, details: e.target.value })}
                    />
                  </div>
                </div>
                <div className="mt-4 flex justify-end">
                  <Button
                    onClick={() =>
                      addLineMutation.mutate({ ...lineForm, batchno: selectedBatchno, capturedat: today() })
                    }
                    disabled={addLineMutation.isPending || !lineForm.accno || !lineForm.amount}
                  >
                    {addLineMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                    Add Line
                  </Button>
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
