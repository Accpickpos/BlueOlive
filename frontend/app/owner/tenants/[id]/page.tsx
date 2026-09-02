'use client';
import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, KeyRound, Plus, Power, PowerOff, Puzzle, Store, Users, X } from 'lucide-react';
import PlatformOwnerRoute from '@/components/PlatformOwnerRoute';
import {
  Tenant,
  Shop,
  TenantUser,
  fetchTenant,
  fetchShops,
  createShop,
  activateShop,
  deactivateShop,
  fetchTenantUsers,
  createTenantAdmin,
  toggleTenantUserStatus,
  resetTenantUserPassword,
  updateTenantAddons,
} from '@/lib/platformApi';

// Keep in sync with backend settings.OPTIONAL_ADDON_APPS / ADDON_DEPENDENCIES.
// Cash Book is NOT an addon - apps/debtors and apps/creditors (both core)
// hard-import it for posting receipts/payments, so it's always enabled.
const ADDON_OPTIONS: { value: string; label: string; requires?: string }[] = [
  { value: 'general_ledger', label: 'General Ledger' },
  { value: 'gas', label: 'Gas (LPG Rentals)', requires: 'general_ledger' },
  { value: 'stockfinder', label: 'Stockfinder' },
];

function TenantDetail() {
  const params = useParams();
  const tenantId = Number(params.id);

  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [shops, setShops] = useState<Shop[]>([]);
  const [users, setUsers] = useState<TenantUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateShop, setShowCreateShop] = useState(false);
  const [showCreateAdmin, setShowCreateAdmin] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [tenantData, shopsData, usersData] = await Promise.all([
        fetchTenant(tenantId),
        fetchShops(tenantId),
        fetchTenantUsers(tenantId),
      ]);
      setTenant(tenantData);
      setShops(shopsData);
      setUsers(usersData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.response?.data?.error || 'Failed to load tenant');
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    load();
  }, [load]);

  const [addonsSaving, setAddonsSaving] = useState(false);

  const handleToggleAddon = async (addon: string) => {
    if (!tenant) return;
    const current = tenant.enabled_addons || [];
    const enabling = !current.includes(addon);
    const option = ADDON_OPTIONS.find((o) => o.value === addon);

    let next: string[];
    if (enabling) {
      // Turning on an addon that requires another auto-enables the
      // dependency too (mirrors backend ADDON_DEPENDENCIES validation,
      // which would otherwise just reject this as a 400).
      const deps = option?.requires ? [option.requires] : [];
      next = Array.from(new Set([...current, addon, ...deps]));
    } else {
      // Turning off a dependency also turns off whatever requires it.
      const dependents = ADDON_OPTIONS.filter((o) => o.requires === addon).map((o) => o.value);
      next = current.filter((a) => a !== addon && !dependents.includes(a));
    }

    setAddonsSaving(true);
    try {
      const updated = await updateTenantAddons(tenant.id, next);
      setTenant(updated);
    } catch (err: any) {
      setError(err?.response?.data?.enabled_addons?.[0] || err?.response?.data?.error || 'Failed to update addons');
    } finally {
      setAddonsSaving(false);
    }
  };

  const handleToggleShop = async (shop: Shop) => {
    setBusyId(shop.id);
    try {
      if (shop.is_active) {
        await deactivateShop(shop.id);
      } else {
        await activateShop(shop.id);
      }
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Action failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleToggleUser = async (user: TenantUser) => {
    setBusyId(user.id);
    try {
      await toggleTenantUserStatus(user.id);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Action failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleResetPassword = async (user: TenantUser) => {
    const newPassword = window.prompt(`New password for ${user.username}:`);
    if (!newPassword) return;
    setBusyId(user.id);
    try {
      await resetTenantUserPassword(user.id, newPassword);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to reset password');
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return <div className="max-w-5xl mx-auto px-6 py-8 text-slate-500 text-sm">Loading...</div>;
  }

  if (!tenant) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-sm text-red-400">{error || 'Tenant not found'}</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <Link href="/owner" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-100 mb-6 w-fit">
        <ArrowLeft className="h-4 w-4" /> Back to tenants
      </Link>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-lg font-semibold">{tenant.name}</h1>
          <p className="text-xs text-slate-500">
            {tenant.subdomain} &middot; {tenant.email}
          </p>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
            tenant.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
          }`}
        >
          {tenant.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded px-3 py-2 mb-4">
          {error}
        </div>
      )}

      {/* Addons */}
      <section className="mb-10">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide flex items-center gap-1.5 mb-3">
          <Puzzle className="h-3.5 w-3.5" /> Addons
        </h2>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
          {ADDON_OPTIONS.map((option) => {
            const enabled = (tenant.enabled_addons || []).includes(option.value);
            return (
              <label
                key={option.value}
                className="flex items-center gap-3 text-sm py-1.5 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={enabled}
                  disabled={addonsSaving}
                  onChange={() => handleToggleAddon(option.value)}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800"
                />
                <span className="text-slate-200">{option.label}</span>
                {option.requires && (
                  <span className="text-xs text-slate-500">requires {ADDON_OPTIONS.find((o) => o.value === option.requires)?.label}</span>
                )}
              </label>
            );
          })}
        </div>
      </section>

      {/* Shops */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
            <Store className="h-3.5 w-3.5" /> Shops
          </h2>
          <button
            onClick={() => setShowCreateShop(true)}
            className="flex items-center gap-1.5 text-sm bg-slate-100 text-slate-900 px-3 py-1.5 rounded-md hover:bg-white transition"
          >
            <Plus className="h-4 w-4" /> New Shop
          </button>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          {shops.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm">No shops yet.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Subdomain</th>
                  <th className="text-left px-4 py-2.5 font-medium">Head Office</th>
                  <th className="text-left px-4 py-2.5 font-medium">Status</th>
                  <th className="text-right px-4 py-2.5 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {shops.map((shop) => (
                  <tr key={shop.id}>
                    <td className="px-4 py-2.5">{shop.name}</td>
                    <td className="px-4 py-2.5 text-slate-400">{shop.subdomain}</td>
                    <td className="px-4 py-2.5 text-slate-400">{shop.is_head_office ? 'Yes' : ''}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                          shop.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
                        }`}
                      >
                        {shop.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={() => handleToggleShop(shop)}
                        disabled={busyId === shop.id}
                        className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md border transition disabled:opacity-50 ${
                          shop.is_active
                            ? 'border-red-900 text-red-400 hover:bg-red-950/50'
                            : 'border-emerald-900 text-emerald-400 hover:bg-emerald-950/50'
                        }`}
                      >
                        {shop.is_active ? (
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
      </section>

      {/* Users */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5" /> Users
          </h2>
          <button
            onClick={() => setShowCreateAdmin(true)}
            className="flex items-center gap-1.5 text-sm bg-slate-100 text-slate-900 px-3 py-1.5 rounded-md hover:bg-white transition"
          >
            <Plus className="h-4 w-4" /> New Admin
          </button>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          {users.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm">No users yet.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Username</th>
                  <th className="text-left px-4 py-2.5 font-medium">Email</th>
                  <th className="text-left px-4 py-2.5 font-medium">Role</th>
                  <th className="text-left px-4 py-2.5 font-medium">Status</th>
                  <th className="text-right px-4 py-2.5 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-2.5">{user.username}</td>
                    <td className="px-4 py-2.5 text-slate-400">{user.email}</td>
                    <td className="px-4 py-2.5 text-slate-400">{user.role}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                          user.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right space-x-2">
                      <button
                        onClick={() => handleResetPassword(user)}
                        disabled={busyId === user.id}
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md border border-slate-700 text-slate-300 hover:bg-slate-800 transition disabled:opacity-50"
                      >
                        <KeyRound className="h-3 w-3" /> Reset Password
                      </button>
                      <button
                        onClick={() => handleToggleUser(user)}
                        disabled={busyId === user.id}
                        className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md border transition disabled:opacity-50 ${
                          user.is_active
                            ? 'border-red-900 text-red-400 hover:bg-red-950/50'
                            : 'border-emerald-900 text-emerald-400 hover:bg-emerald-950/50'
                        }`}
                      >
                        {user.is_active ? (
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
      </section>

      {showCreateShop && (
        <CreateShopModal
          tenantId={tenantId}
          onClose={() => setShowCreateShop(false)}
          onCreated={() => {
            setShowCreateShop(false);
            load();
          }}
        />
      )}

      {showCreateAdmin && (
        <CreateAdminModal
          tenantId={tenantId}
          onClose={() => setShowCreateAdmin(false)}
          onCreated={() => {
            setShowCreateAdmin(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function CreateShopModal({
  tenantId,
  onClose,
  onCreated,
}: {
  tenantId: number;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({ name: '', code: '', address: '', phone: '', email: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await createShop({ tenant_id: tenantId, ...form });
      onCreated();
    } catch (err: any) {
      const data = err?.response?.data;
      setError(
        typeof data === 'string'
          ? data
          : data?.error || data?.detail || Object.values(data || {}).flat().join(' ') || 'Failed to create shop'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New Shop" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {error && <ErrorBox message={error} />}
        <Field label="Shop Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required />
        <Field label="Code" value={form.code} onChange={(v) => setForm({ ...form, code: v })} />
        <Field label="Address" value={form.address} onChange={(v) => setForm({ ...form, address: v })} />
        <Field label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
        <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
        <SubmitButton saving={saving} label="Create Shop" />
      </form>
    </Modal>
  );
}

function CreateAdminModal({
  tenantId,
  onClose,
  onCreated,
}: {
  tenantId: number;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await createTenantAdmin({ tenant_id: tenantId, ...form });
      onCreated();
    } catch (err: any) {
      const data = err?.response?.data;
      setError(
        typeof data === 'string'
          ? data
          : data?.error || data?.errors?.join(' ') || 'Failed to create admin user'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New Tenant Admin" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {error && <ErrorBox message={error} />}
        <Field label="Username" value={form.username} onChange={(v) => setForm({ ...form, username: v })} required />
        <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
        <Field label="First Name" value={form.first_name} onChange={(v) => setForm({ ...form, first_name: v })} />
        <Field label="Last Name" value={form.last_name} onChange={(v) => setForm({ ...form, last_name: v })} />
        <Field
          label="Password"
          type="password"
          value={form.password}
          onChange={(v) => setForm({ ...form, password: v })}
          required
        />
        <SubmitButton saving={saving} label="Create Admin" />
      </form>
    </Modal>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-slate-900 border border-slate-800 rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded px-3 py-2">{message}</div>
  );
}

function SubmitButton({ saving, label }: { saving: boolean; label: string }) {
  return (
    <button
      type="submit"
      disabled={saving}
      className="w-full bg-slate-100 text-slate-900 font-medium py-2 rounded-md text-sm hover:bg-white transition disabled:opacity-50 mt-2"
    >
      {saving ? 'Saving...' : label}
    </button>
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

export default function TenantDetailPage() {
  return (
    <PlatformOwnerRoute>
      <TenantDetail />
    </PlatformOwnerRoute>
  );
}
