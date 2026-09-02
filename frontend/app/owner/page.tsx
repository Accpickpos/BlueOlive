'use client';
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { KeyRound, LogOut, Plus, Power, PowerOff, Shield, X } from 'lucide-react';
import PlatformOwnerRoute from '@/components/PlatformOwnerRoute';
import { usePlatformAuth } from '@/lib/PlatformAuthContext';
import {
  Tenant,
  TenantStats,
  fetchTenants,
  fetchTenantStats,
  createTenant,
  activateTenant,
  deactivateTenant,
} from '@/lib/platformApi';

function OwnerDashboard() {
  const { owner, logout } = usePlatformAuth();
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, tenantsData] = await Promise.all([fetchTenantStats(), fetchTenants()]);
      setStats(statsData);
      setTenants(tenantsData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load tenants');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleToggle = async (tenant: Tenant) => {
    setBusyId(tenant.id);
    try {
      if (tenant.is_active) {
        await deactivateTenant(tenant.id);
      } else {
        await activateTenant(tenant.id);
      }
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.response?.data?.message || 'Action failed');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-slate-400" />
          <div>
            <h1 className="text-lg font-semibold">Platform Owner</h1>
            <p className="text-xs text-slate-500">Signed in as {owner?.username}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/owner/superusers"
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-100 transition"
          >
            <KeyRound className="h-4 w-4" /> Owner Accounts
          </Link>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-100 transition"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <StatCard label="Tenants" value={stats.total_tenants} />
          <StatCard label="Active" value={stats.active_tenants} accent="text-emerald-400" />
          <StatCard label="Inactive" value={stats.inactive_tenants} accent="text-red-400" />
          <StatCard label="Shops" value={stats.total_shops} />
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide">Tenants</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 text-sm bg-slate-100 text-slate-900 px-3 py-1.5 rounded-md hover:bg-white transition"
        >
          <Plus className="h-4 w-4" /> New Tenant
        </button>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded px-3 py-2 mb-4">
          {error}
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">Loading...</div>
        ) : tenants.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No tenants yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Name</th>
                <th className="text-left px-4 py-2.5 font-medium">Subdomain</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Setup</th>
                <th className="text-left px-4 py-2.5 font-medium">Shops</th>
                <th className="text-right px-4 py-2.5 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {tenants.map((tenant) => (
                <tr key={tenant.id}>
                  <td className="px-4 py-2.5">
                    <Link href={`/owner/tenants/${tenant.id}`} className="hover:underline">
                      {tenant.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">{tenant.subdomain}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                        tenant.is_active
                          ? 'bg-emerald-950 text-emerald-400'
                          : 'bg-red-950 text-red-400'
                      }`}
                    >
                      {tenant.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">{tenant.setup_status}</td>
                  <td className="px-4 py-2.5 text-slate-400">{tenant.shops?.length ?? 0}</td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => handleToggle(tenant)}
                      disabled={busyId === tenant.id}
                      className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md border transition disabled:opacity-50 ${
                        tenant.is_active
                          ? 'border-red-900 text-red-400 hover:bg-red-950/50'
                          : 'border-emerald-900 text-emerald-400 hover:bg-emerald-950/50'
                      }`}
                    >
                      {tenant.is_active ? (
                        <>
                          <PowerOff className="h-3 w-3" /> Deactivate
                        </>
                      ) : (
                        <>
                          <Power className="h-3 w-3" /> Activate
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CreateTenantModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-3">
      <div className={`text-2xl font-semibold ${accent || 'text-slate-100'}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function CreateTenantModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await createTenant(form);
      onCreated();
    } catch (err: any) {
      const data = err?.response?.data;
      setError(
        typeof data === 'string'
          ? data
          : data?.detail || Object.values(data || {}).flat().join(' ') || 'Failed to create tenant'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-slate-900 border border-slate-800 rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">New Tenant</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && (
            <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded px-3 py-2">
              {error}
            </div>
          )}

          <Field label="Company / Tenant Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required />
          <Field label="Admin Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
          <Field label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} required />
          <Field
            label="Initial Admin Password"
            type="password"
            value={form.password}
            onChange={(v) => setForm({ ...form, password: v })}
            required
          />

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-slate-100 text-slate-900 font-medium py-2 rounded-md text-sm hover:bg-white transition disabled:opacity-50 mt-2"
          >
            {saving ? 'Creating...' : 'Create Tenant'}
          </button>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
      />
    </div>
  );
}

export default function OwnerPage() {
  return (
    <PlatformOwnerRoute>
      <OwnerDashboard />
    </PlatformOwnerRoute>
  );
}
