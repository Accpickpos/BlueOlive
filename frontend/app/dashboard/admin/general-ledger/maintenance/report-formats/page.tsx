'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glReportFormatsApi } from '@/lib/general-ledger';
import { GLRep, GLRepCreateData } from '@/lib/types/generalLedger';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Plus, Pencil, Trash2, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const emptyForm: GLRepCreateData = {
  type: 'I',
  fieldtype: 'D',
  line: 1,
  printdet: 'N',
  name: '',
  start: 1,
  endcalc: 1,
};

export default function ReportFormatsPage() {
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState<'I' | 'B'>('I');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRow, setEditingRow] = useState<GLRep | null>(null);
  const [formData, setFormData] = useState<GLRepCreateData>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['gl-report-formats', typeFilter],
    queryFn: () => glReportFormatsApi.list({ type: typeFilter, ordering: 'line' }),
  });

  const createMutation = useMutation({
    mutationFn: (body: GLRepCreateData) => glReportFormatsApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-report-formats'] });
      setIsDialogOpen(false);
      setFormError(null);
    },
    onError: (err) => setFormError(getApiErrorMessage(err, 'Failed to create row')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<GLRepCreateData> }) =>
      glReportFormatsApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-report-formats'] });
      setIsDialogOpen(false);
      setEditingRow(null);
      setFormError(null);
    },
    onError: (err) => setFormError(getApiErrorMessage(err, 'Failed to update row')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => glReportFormatsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gl-report-formats'] }),
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to delete row')),
  });

  const handleEdit = (row: GLRep) => {
    setEditingRow(row);
    setFormData({
      type: row.type,
      fieldtype: row.fieldtype,
      line: row.line,
      printdet: row.printdet,
      name: row.name,
      start: row.start,
      endcalc: row.endcalc,
    });
    setFormError(null);
    setIsDialogOpen(true);
  };

  const handleDelete = (row: GLRep) => {
    if (window.confirm(`Delete report format line ${row.line} - ${row.name}?`)) {
      deleteMutation.mutate(row.id);
    }
  };

  const handleSubmit = () => {
    if (editingRow) {
      updateMutation.mutate({ id: editingRow.id, body: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const rows = data?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/general-ledger/maintenance">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Report Formats</h1>
          <p className="text-gray-600 mt-1">
            Layout rows for Income Statement / Balance Sheet. Detail rows sum account
            report lines (repline); Heading/Total/Subtotal rows sum earlier report lines.
          </p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-2">
            <Button
              variant={typeFilter === 'I' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter('I')}
            >
              Income Statement
            </Button>
            <Button
              variant={typeFilter === 'B' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter('B')}
            >
              Balance Sheet
            </Button>
          </div>
          <Button
            onClick={() => {
              setFormData({ ...emptyForm, type: typeFilter });
              setEditingRow(null);
              setFormError(null);
              setIsDialogOpen(true);
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Line
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
          </div>
        ) : rows.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No report format lines defined for this report type yet.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Line</TableHead>
                <TableHead>Field Type</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Start</TableHead>
                <TableHead>End Calc</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.line}</TableCell>
                  <TableCell>{row.fieldtype_display}</TableCell>
                  <TableCell>{row.name}</TableCell>
                  <TableCell>{row.start}</TableCell>
                  <TableCell>{row.endcalc}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(row)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(row)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingRow ? 'Edit Report Line' : 'Add Report Line'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {formError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                {formError}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Line #</label>
                <Input
                  type="number"
                  value={formData.line}
                  onChange={(e) => setFormData({ ...formData, line: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Field Type</label>
                <select
                  value={formData.fieldtype}
                  onChange={(e) => setFormData({ ...formData, fieldtype: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="H">Heading</option>
                  <option value="D">Detail</option>
                  <option value="S">Subtotal</option>
                  <option value="T">Total</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                maxLength={30}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">
                  Start {formData.fieldtype === 'D' ? '(account repline)' : '(report line)'}
                </label>
                <Input
                  type="number"
                  value={formData.start}
                  onChange={(e) => setFormData({ ...formData, start: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  End Calc {formData.fieldtype === 'D' ? '(account repline)' : '(report line)'}
                </label>
                <Input
                  type="number"
                  value={formData.endcalc}
                  onChange={(e) => setFormData({ ...formData, endcalc: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
              {createMutation.isPending || updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              {editingRow ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
