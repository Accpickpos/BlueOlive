'use client';

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { glIntegrationApi } from '@/lib/general-ledger';
import { GLIntegrationSettings } from '@/lib/types/generalLedger';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

type FieldKey = Exclude<keyof GLIntegrationSettings, 'id' | 'created_at' | 'updated_at'>;

const FIELDS: { key: FieldKey; label: string; help: string }[] = [
  { key: 'debtors_control_accno', label: 'Debtors Control', help: 'Debtors subledger control account' },
  { key: 'creditors_control_accno', label: 'Creditors Control', help: 'Creditors subledger control account' },
  { key: 'bank_control_accno', label: 'Bank Control', help: 'Default bank account for BANK cash book transactions' },
  { key: 'cash_control_accno', label: 'Cash Control', help: 'Default cash account for CASH cash book transactions' },
  { key: 'sales_accno', label: 'Sales', help: 'Revenue account for debtors invoices/cash sales' },
  { key: 'vat_output_accno', label: 'VAT Output', help: 'VAT payable on sales/income' },
  { key: 'vat_input_accno', label: 'VAT Input', help: 'VAT receivable on purchases/expenses' },
  { key: 'stock_control_accno', label: 'Stock Control', help: 'Inventory asset account' },
  { key: 'stock_shrinkage_expense_accno', label: 'Stock Shrinkage Expense', help: 'Stock take net losses' },
  { key: 'stock_gain_income_accno', label: 'Stock Gain Income', help: 'Stock take net gains' },
  { key: 'debtors_interest_income_accno', label: 'Debtors Interest Income', help: 'Interest charged to debtors' },
  { key: 'debtors_suspense_accno', label: 'Debtors Suspense', help: 'Offsetting account for manual debtor journals (JD/JC)' },
  { key: 'creditors_discount_received_accno', label: 'Discount Received', help: 'Settlement discount on creditor payments (optional)' },
  { key: 'creditors_suspense_accno', label: 'Creditors Suspense', help: 'Offsetting account for manual creditor journals' },
  { key: 'cashbook_default_income_accno', label: 'Cash Book Default Income', help: 'Fallback when an income category has no GL account mapped' },
  { key: 'cashbook_default_expense_accno', label: 'Cash Book Default Expense', help: 'Fallback when an expense category has no GL account mapped' },
];

export default function IntegrationSettingsPage() {
  const queryClient = useQueryClient();
  const [formState, setFormState] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['gl-integration-settings'],
    queryFn: () => glIntegrationApi.getSettings(),
  });

  useEffect(() => {
    if (settings) {
      const next: Record<string, string> = {};
      FIELDS.forEach((f) => {
        const value = settings[f.key];
        next[f.key] = value === null || value === undefined ? '' : String(value);
      });
      setFormState(next);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: () => {
      const body: Partial<GLIntegrationSettings> = {};
      FIELDS.forEach((f) => {
        const raw = formState[f.key];
        (body as any)[f.key] = raw ? parseInt(raw) : null;
      });
      return glIntegrationApi.updateSettings(body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gl-integration-settings'] });
      setMessage({ type: 'success', text: 'Integration settings saved.' });
    },
    onError: (err) => setMessage({ type: 'error', text: getApiErrorMessage(err, 'Failed to save settings') }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold">Integration Settings</h1>
          <p className="text-gray-600 mt-1">
            Control-account mapping the Integration Transfer pipeline uses to post
            Debtors/Creditors/Stock Control/Cash Book transactions into GL.
          </p>
        </div>
      </div>

      {message && (
        <div
          className={`rounded p-3 text-sm border ${
            message.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FIELDS.map((f) => (
            <div key={f.key}>
              <label className="text-sm font-medium">{f.label}</label>
              <p className="text-xs text-gray-500 mb-1">{f.help}</p>
              <Input
                type="number"
                value={formState[f.key] ?? ''}
                onChange={(e) => setFormState({ ...formState, [f.key]: e.target.value })}
                placeholder="Account number"
              />
            </div>
          ))}
        </div>
        <div className="mt-6 flex justify-end">
          <Button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Save Settings
          </Button>
        </div>
      </Card>
    </div>
  );
}
