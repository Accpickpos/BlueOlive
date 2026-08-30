'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glMasterApi } from '@/lib/general-ledger';
import { GLMastListItem, GLMastCreateData } from '@/lib/types/generalLedger';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Plus, Pencil, Trash2, Search, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const emptyForm: GLMastCreateData = {
  accno: 0,
  name: '',
  type: 'I',
  drorcr: 'D',
  repline: 1,
  balbfwd: 0,
};

export default function ChartOfAccountsPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<GLMastListItem | null>(null);
  const [formData, setFormData] = useState<GLMastCreateData>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['gl-accounts', searchTerm],
    queryFn: () => glMasterApi.list({ search: searchTerm || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: (body: GLMastCreateData) => glMasterApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-accounts'] });
      setIsDialogOpen(false);
      setFormError(null);
    },
    onError: (err) => setFormError(getApiErrorMessage(err, 'Failed to create account')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<GLMastCreateData> }) =>
      glMasterApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-accounts'] });
      setIsDialogOpen(false);
      setEditingAccount(null);
      setFormError(null);
    },
    onError: (err) => setFormError(getApiErrorMessage(err, 'Failed to update account')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => glMasterApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['gl-accounts'] }),
    onError: (err) => window.alert(getApiErrorMessage(err, 'Failed to delete account')),
  });

  const handleEdit = (account: GLMastListItem) => {
    setEditingAccount(account);
    setFormData({
      accno: account.accno,
      name: account.name,
      type: account.type,
      drorcr: account.drorcr,
      repline: account.repline,
      balbfwd: account.balbfwd,
    });
    setFormError(null);
    setIsDialogOpen(true);
  };

  const handleDelete = (account: GLMastListItem) => {
    if (window.confirm(`Delete account ${account.accno} - ${account.name}?`)) {
      deleteMutation.mutate(account.id);
    }
  };

  const handleSubmit = () => {
    if (editingAccount) {
      updateMutation.mutate({ id: editingAccount.id, body: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const accounts = data?.results || [];

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
          <h1 className="text-3xl font-bold">Chart of Accounts</h1>
          <p className="text-gray-600 mt-1">GL master accounts — income statement and balance sheet</p>
        </div>
      </div>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search by account number or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            onClick={() => {
              setFormData(emptyForm);
              setEditingAccount(null);
              setFormError(null);
              setIsDialogOpen(true);
            }}
            className="ml-4"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading accounts...</p>
          </div>
        ) : accounts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No accounts found. Click "Add Account" to create one.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account No.</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Dr/Cr</TableHead>
                <TableHead>Report Line</TableHead>
                <TableHead className="text-right">Balance B/F</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accounts.map((account) => (
                <TableRow key={account.id}>
                  <TableCell className="font-medium">{account.accno}</TableCell>
                  <TableCell>{account.name}</TableCell>
                  <TableCell>
                    <Badge variant={account.type === 'B' ? 'default' : 'secondary'}>
                      {account.type_display}
                    </Badge>
                  </TableCell>
                  <TableCell>{account.drorcr_display}</TableCell>
                  <TableCell>{account.repline}</TableCell>
                  <TableCell className="text-right">
                    {account.balbfwd.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(account)}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(account)}
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
            <DialogTitle>{editingAccount ? 'Edit Account' : 'Add Account'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {formError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                {formError}
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Account Number</label>
              <Input
                type="number"
                value={formData.accno}
                disabled={!!editingAccount}
                onChange={(e) => setFormData({ ...formData, accno: parseInt(e.target.value) || 0 })}
                placeholder="e.g., 4000"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Account Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Sales"
                maxLength={30}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as 'I' | 'B' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="I">Income Statement</option>
                  <option value="B">Balance Sheet</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Dr/Cr</label>
                <select
                  value={formData.drorcr}
                  onChange={(e) => setFormData({ ...formData, drorcr: e.target.value as 'D' | 'C' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="D">Debit</option>
                  <option value="C">Credit</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Report Line</label>
                <Input
                  type="number"
                  value={formData.repline}
                  onChange={(e) => setFormData({ ...formData, repline: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Balance B/F</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.balbfwd}
                  onChange={(e) => setFormData({ ...formData, balbfwd: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {createMutation.isPending || updateMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : null}
              {editingAccount ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
