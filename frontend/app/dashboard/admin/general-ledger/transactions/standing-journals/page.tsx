'use client';

import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glStandingJournalsApi } from '@/lib/general-ledger';
import { GLStJnl, GLStJnlCreateData } from '@/lib/types/generalLedger';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Loader2, Plus, Trash2, PlayCircle } from 'lucide-react';
import Link from 'next/link';

function emptyLine(journalno: number): GLStJnlCreateData {
  return {
    accno: 0,
    details: '',
    drorcr: 'D',
    amount: 0,
    frequency: 1,
    stperiod: 1,
    times: 12,
    nextperiod: 1,
    descriptor: '',
    journalno,
  };
}

export default function StandingJournalsPage() {
  const queryClient = useQueryClient();
  const [selectedJournalno, setSelectedJournalno] = useState<number | null>(null);
  const [newJournalno, setNewJournalno] = useState('');
  const [lineForm, setLineForm] = useState<GLStJnlCreateData>(emptyLine(0));
  const [error, setError] = useState<string | null>(null);

  const { data: allJournals, isLoading: listLoading } = useQuery({
    queryKey: ['gl-standing-journals-all'],
    queryFn: () => glStandingJournalsApi.list({ ordering: 'journalno', page_size: 500 }),
  });

  const journalGroups = useMemo(() => {
    const rows = allJournals?.results || [];
    const groups = new Map<number, { count: number; timesbal: number; times: number }>();
    rows.forEach((row) => {
      const g = groups.get(row.journalno) || { count: 0, timesbal: row.timesbal, times: row.times };
      g.count += 1;
      groups.set(row.journalno, g);
    });
    return Array.from(groups.entries()).sort((a, b) => a[0] - b[0]);
  }, [allJournals]);

  const { data: linesForSelected, isLoading: linesLoading } = useQuery({
    queryKey: ['gl-standing-journal-lines', selectedJournalno],
    queryFn: () => glStandingJournalsApi.list({ journalno: selectedJournalno }),
    enabled: selectedJournalno !== null,
  });

  const { data: balanceCheck } = useQuery({
    queryKey: ['gl-standing-journal-balance', selectedJournalno],
    queryFn: () => glStandingJournalsApi.validateBalance(selectedJournalno as number),
    enabled: selectedJournalno !== null,
  });

  const addLineMutation = useMutation({
    mutationFn: (body: GLStJnlCreateData) => glStandingJournalsApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journal-lines', selectedJournalno] });
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journal-balance', selectedJournalno] });
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journals-all'] });
      setLineForm(emptyLine(selectedJournalno || 0));
      setError(null);
    },
    onError: (err) => setError(getApiErrorMessage(err, 'Failed to add line')),
  });

  const deleteLineMutation = useMutation({
    mutationFn: (id: number) => glStandingJournalsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journal-lines', selectedJournalno] });
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journal-balance', selectedJournalno] });
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journals-all'] });
    },
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to delete line')),
  });

  const postDueMutation = useMutation({
    mutationFn: () => glStandingJournalsApi.postDue(),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['gl-standing-journals-all'] });
      window.alert(
        `Posted: ${result.journals_posted.join(', ') || 'none'}\n` +
        `Skipped (unbalanced): ${result.journals_skipped_unbalanced.join(', ') || 'none'}\n` +
        `Completed: ${result.journals_completed.join(', ') || 'none'}`
      );
    },
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to post due journals')),
  });

  const startNewJournal = () => {
    const n = parseInt(newJournalno);
    if (!n) {
      setError('Enter a journal number to start capturing.');
      return;
    }
    setSelectedJournalno(n);
    setLineForm(emptyLine(n));
    setError(null);
  };

  const lines = linesForSelected?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/admin/general-ledger/transactions">
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Standing Journals</h1>
            <p className="text-gray-600 mt-1">Recurring journals — define once, post the ones due each period</p>
          </div>
        </div>
        <Button onClick={() => postDueMutation.mutate()} disabled={postDueMutation.isPending}>
          {postDueMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <PlayCircle className="w-4 h-4 mr-2" />}
          Post Due Journals
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 md:col-span-1">
          <h2 className="text-lg font-bold mb-4">Journals</h2>

          <div className="flex gap-2 mb-4">
            <Input
              type="number"
              placeholder="New journal #"
              value={newJournalno}
              onChange={(e) => setNewJournalno(e.target.value)}
            />
            <Button size="sm" onClick={startNewJournal}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {listLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : journalGroups.length === 0 ? (
            <p className="text-sm text-gray-500">No standing journals yet.</p>
          ) : (
            <div className="space-y-1">
              {journalGroups.map(([journalno, g]) => (
                <button
                  key={journalno}
                  onClick={() => setSelectedJournalno(journalno)}
                  className={`w-full text-left px-3 py-2 rounded text-sm flex justify-between items-center ${
                    selectedJournalno === journalno ? 'bg-blue-50 border border-blue-300' : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <span>
                    Journal {journalno} <span className="text-gray-400">({g.count} lines)</span>
                  </span>
                  <span className="text-xs text-gray-500">{g.timesbal}/{g.times}</span>
                </button>
              ))}
            </div>
          )}
        </Card>

        <div className="md:col-span-2 space-y-4">
          {selectedJournalno === null ? (
            <Card className="p-6 text-center text-gray-500">
              Select an existing journal or start a new one.
            </Card>
          ) : (
            <>
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold">Journal {selectedJournalno}</h2>
                  {balanceCheck && (
                    <Badge variant={balanceCheck.is_balanced ? 'default' : 'destructive'}>
                      {balanceCheck.is_balanced ? 'Balanced' : 'Unbalanced'}
                    </Badge>
                  )}
                </div>

                {balanceCheck && (
                  <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                    <div>
                      <p className="text-gray-500">Total Debit</p>
                      <p className="font-bold">{balanceCheck.total_debit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Total Credit</p>
                      <p className="font-bold">{balanceCheck.total_credit.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</p>
                    </div>
                  </div>
                )}

                {linesLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : lines.length === 0 ? (
                  <p className="text-sm text-gray-500">No lines captured yet.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account</TableHead>
                        <TableHead>Dr/Cr</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Next Period</TableHead>
                        <TableHead>Progress</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lines.map((line: GLStJnl) => (
                        <TableRow key={line.id}>
                          <TableCell>{line.accno}</TableCell>
                          <TableCell>{line.drorcr_display}</TableCell>
                          <TableCell className="text-right">
                            {line.amount.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell>{line.nextperiod}</TableCell>
                          <TableCell>{line.timesbal}/{line.times}</TableCell>
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
                    <label className="text-sm font-medium">Times (occurrences)</label>
                    <Input
                      type="number"
                      min={1}
                      max={999}
                      value={lineForm.times}
                      onChange={(e) => setLineForm({ ...lineForm, times: parseInt(e.target.value) || 1 })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Start Period</label>
                    <Input
                      type="number"
                      min={1}
                      max={12}
                      value={lineForm.stperiod}
                      onChange={(e) => setLineForm({ ...lineForm, stperiod: parseInt(e.target.value) || 1 })}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Next Period</label>
                    <Input
                      type="number"
                      min={1}
                      max={12}
                      value={lineForm.nextperiod}
                      onChange={(e) => setLineForm({ ...lineForm, nextperiod: parseInt(e.target.value) || 1 })}
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
                      addLineMutation.mutate({ ...lineForm, journalno: selectedJournalno })
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
