'use client';
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, KeyRound, Plus, Power, PowerOff, X } from 'lucide-react';
import PlatformOwnerRoute from '@/components/PlatformOwnerRoute';
import { usePlatformAuth } from '@/lib/PlatformAuthContext';
import {
  Superuser,
  fetchSuperusers,
  createSuperuser,
  toggleSuperuserActive,
  setSuperuserPassword,
} from '@/lib/platformApi';

function SuperusersPage() {
  const { owner } = usePlatformAuth();
  const [superusers, setSuperusers] = useState<Superuser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setSuperusers(await fetchSuperusers());
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load owner accounts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleToggle = async (user: Superuser) => {
    setBusyId(user.id);
    try {
      await toggleSuperuserActive(user.id);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Action failed');
    } finally {
      setBusyId(null);
    }
  };

  const handleResetPassword = async (user: Superuser) => {
    const newPassword = window.prompt(`New password for ${user.username}:`);
    if (!newPassword) return;
    setBusyId(user.id);
    try {
      await setSuperuserPassword(user.id, newPassword);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to reset password');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <Link href="/owner" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-100 mb-6 w-fit">
        <ArrowLeft className="h-4 w-4" /> Back to tenants
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-semibold">Owner Accounts</h1>
          <p className="text-xs text-slate-500">Django superuser accounts with full platform access</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 text-sm bg-slate-100 text-slate-900 px-3 py-1.5 rounded-md hover:bg-white transition"
        >
          <Plus className="h-4 w-4" /> New Owner Account
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
        ) : superusers.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No owner accounts found.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Username</th>
                <th className="text-left px-4 py-2.5 font-medium">Email</th>
                <th className="text-left px-4 py-2.5 font-medium">Status</th>
                <th className="text-right px-4 py-2.5 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {superusers.map((user) => (
                <tr key={user.id}>
                  <td className="px-4 py-2.5">
                    {user.username}
                    {user.username === owner?.username && (
                      <span className="ml-2 text-xs text-slate-500">(you)</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-400">{user.email}</td>
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
                      onClick={() => handleToggle(user)}
                      disabled={busyId === user.id || user.username === owner?.username}
                      title={user.username === owner?.username ? "You can't deactivate your own account" : undefined}
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

      {showCreate && (
        <CreateSuperuserModal
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

function CreateSuperuserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await createSuperuser(form);
      onCreated();
    } catch (err: any) {
      const data = err?.response?.data;
      setError(
        typeof data === 'string'
          ? data
          : data?.detail || Object.values(data || {}).flat().join(' ') || 'Failed to create owner account'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-slate-900 border border-slate-800 rounded-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">New Owner Account</h3>
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

          <div>
            <label className="block text-sm text-slate-400 mb-1">Username</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full bg-slate-100 text-slate-900 font-medium py-2 rounded-md text-sm hover:bg-white transition disabled:opacity-50 mt-2"
          >
            {saving ? 'Creating...' : 'Create Owner Account'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function OwnerSuperusersPage() {
  return (
    <PlatformOwnerRoute>
      <SuperusersPage />
    </PlatformOwnerRoute>
  );
}
