'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield } from 'lucide-react';
import { usePlatformAuth } from '@/lib/PlatformAuthContext';

export default function OwnerLoginPage() {
  const { login } = usePlatformAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      router.push('/owner');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="bg-slate-800 rounded-full p-3 mb-3">
            <Shield className="h-6 w-6 text-slate-300" />
          </div>
          <h1 className="text-xl font-semibold">Platform Owner</h1>
          <p className="text-sm text-slate-400">BlueOlive superuser access</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4">
          {error && (
            <div className="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded px-3 py-2">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm text-slate-400 mb-1" htmlFor="owner-username">Username</label>
            <input
              id="owner-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              autoComplete="username"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1" htmlFor="owner-password">Password</label>
            <input
              id="owner-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-500"
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-100 text-slate-900 font-medium py-2 rounded-md text-sm hover:bg-white transition disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
