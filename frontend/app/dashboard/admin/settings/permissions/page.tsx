'use client';

import { useEffect, useState } from 'react';
import {
  accessGrantsApi,
  AccessGrant,
  ROLES,
  MODULES,
  FUNCTION_TYPES,
  Role,
  Module,
  FunctionType,
} from '@/lib/common/accessGrants';
import { getApiErrorMessage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, Info } from 'lucide-react';
import Link from 'next/link';

const MODULE_LABELS: Record<Module, string> = {
  pos: 'Point of Sale',
  debtors: 'Debtors',
  creditors: 'Creditors',
  cash_book: 'Cash Book',
  general_ledger: 'General Ledger',
  stock_control: 'Stock Control',
  purchase_orders: 'Purchase Orders',
  settings: 'Utilities',
};

const FUNCTION_LABELS: Record<FunctionType, string> = {
  MAINTENANCE: 'Maintenance',
  TRANSACTIONS: 'Transactions',
  ENQUIRY: 'Enquiry',
  REPORT: 'Report',
};

function key(role: Role, module: Module, functionType: FunctionType) {
  return `${role}|${module}|${functionType}`;
}

export default function AccessGrantsPage() {
  const [grants, setGrants] = useState<Map<string, AccessGrant>>(new Map());
  const [pendingChanges, setPendingChanges] = useState<Map<string, boolean>>(new Map());
  const [selectedRole, setSelectedRole] = useState<Role>('MANAGER');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await accessGrantsApi.list();
      const map = new Map<string, AccessGrant>();
      data.forEach((g) => map.set(key(g.role, g.module, g.function_type), g));
      setGrants(map);
      setPendingChanges(new Map());
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load access grants'));
    } finally {
      setLoading(false);
    }
  }

  function isAllowed(role: Role, module: Module, functionType: FunctionType) {
    const k = key(role, module, functionType);
    if (pendingChanges.has(k)) return pendingChanges.get(k)!;
    return grants.get(k)?.is_allowed ?? false;
  }

  function toggle(role: Role, module: Module, functionType: FunctionType) {
    const k = key(role, module, functionType);
    const current = isAllowed(role, module, functionType);
    const next = new Map(pendingChanges);
    next.set(k, !current);
    setPendingChanges(next);
  }

  async function saveChanges() {
    if (pendingChanges.size === 0) return;
    setSaving(true);
    setError(null);
    try {
      const payload = Array.from(pendingChanges.entries()).map(([k, is_allowed]) => {
        const [role, module, function_type] = k.split('|') as [Role, Module, FunctionType];
        return { role, module, function_type, is_allowed };
      });
      const result = await accessGrantsApi.bulkUpdate(payload);
      setMessage(`Saved ${result.updated} change${result.updated === 1 ? '' : 's'}.`);
      await load();
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save changes'));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/settings">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Access Grants</h1>
          <p className="text-gray-600 mt-1">Role × Module × Function permission matrix (manual §8.1 foundation)</p>
        </div>
      </div>

      <Card className="p-4 flex items-start gap-2 bg-amber-50 border-amber-200">
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-700" />
        <p className="text-sm text-amber-800">
          This matrix is not yet enforced anywhere in the app — no screen or API checks it yet. It exists so the
          rollout (module by module) has a real permission source to adopt, without risking any existing access
          control.
        </p>
      </Card>

      {error && <div className="rounded p-3 text-sm border bg-red-50 border-red-200 text-red-800">{error}</div>}
      {message && <div className="rounded p-3 text-sm border bg-green-50 border-green-200 text-green-800">{message}</div>}

      <Card className="p-4">
        <div className="flex flex-wrap gap-2">
          {ROLES.map((role) => (
            <button
              key={role}
              onClick={() => setSelectedRole(role)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                selectedRole === role ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {role}
            </button>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2 pr-4">Module</th>
                {FUNCTION_TYPES.map((ft) => (
                  <th key={ft} className="py-2 px-2 text-center">
                    {FUNCTION_LABELS[ft]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MODULES.map((module) => (
                <tr key={module} className="border-b">
                  <td className="py-2 pr-4 font-medium">{MODULE_LABELS[module]}</td>
                  {FUNCTION_TYPES.map((ft) => {
                    const k = key(selectedRole, module, ft);
                    const allowed = isAllowed(selectedRole, module, ft);
                    const changed = pendingChanges.has(k);
                    return (
                      <td key={ft} className="py-2 px-2 text-center">
                        <input
                          type="checkbox"
                          checked={allowed}
                          onChange={() => toggle(selectedRole, module, ft)}
                          className={`h-4 w-4 ${changed ? 'ring-2 ring-amber-400' : ''}`}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={saveChanges} disabled={saving || pendingChanges.size === 0}>
          {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
          Save {pendingChanges.size > 0 ? `${pendingChanges.size} Change${pendingChanges.size === 1 ? '' : 's'}` : 'Changes'}
        </Button>
        {pendingChanges.size > 0 && (
          <Button variant="outline" onClick={() => setPendingChanges(new Map())}>
            Discard
          </Button>
        )}
      </div>
    </div>
  );
}
