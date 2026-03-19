'use client';

import { useState, useEffect } from 'react';
import { login, fetchCSRFToken, getTenantShops } from '@/lib/api';
import { useAuthContext } from '@/lib/AuthContext';
import { setTenant, setShops, setCurrentShop, type Shop } from '@/lib/shopContext';

interface LoginUser {
  id: number;
  username: string;
  role: string;
  is_superuser: boolean;
  is_admin: boolean;
}

export default function LoginPage() {
  const [subdomain, setSubdomain] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messageType, setMessageType] = useState<'error' | 'success'>('error');
  const { setUser } = useAuthContext();

  // Pre-fetch CSRF token on page load
  useEffect(() => {
    fetchCSRFToken().catch(() => {
      console.log('CSRF token pre-fetch initiated');
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (!subdomain || !username || !password) {
      setMessage('Please fill in all fields');
      setMessageType('error');
      setLoading(false);
      return;
    }

    try {
      console.log('Attempting login with:', { subdomain, username });
      const response = await login(subdomain, username, password);
      console.log('Login response:', response);
      console.log('Login response data:', response.data);
      
      if (response.status === 200) {
        console.log('Login successful!');
        setMessage('Login successful! Redirecting...');
        setMessageType('success');
        
        // Store tenant in localStorage for API requests
        setTenant(subdomain);
        console.log('Stored tenant in localStorage:', subdomain);
        
        // Use the shop from the login response (already set by backend)
        const shop = response.data.shop;
        const shops = response.data.accessible_shops || [];
        
        setShops(shops);
        
        if (shop) {
          // Use the shop selected during login (or default set by backend)
          setCurrentShop(shop);
          console.log('Set current shop:', shop.name);
        } else if (shops.length > 0) {
          // Fallback to first shop if no shop in response
          setCurrentShop(shops[0]);
          console.log('Set current shop:', shops[0].name);
        }
        
        // Set user directly from login response to bypass profile fetch issues
        const userData: LoginUser = response.data.user;
        const user = {
          id: userData.id,
          username: userData.username,
          email: userData.username, // Use username as email fallback
          role: userData.role,
          is_superuser: userData.is_superuser,
          is_admin: userData.is_admin,
          tenant_id: null,
        };
        setUser(user);
        console.log('Set user in AuthContext:', user);
        
        // Force redirect using window.location for reliability
        console.log('Attempting redirect to /dashboard');
        window.location.href = '/dashboard';
      }
    } catch (error: any) {
      console.error('Login error:', error);
      const errorMsg = 
        error?.response?.data?.detail || 
        error?.message ||
        'Login failed. Please check your credentials.';
      setMessage(errorMsg);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 py-12 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">BlueOlive</h1>
          <p className="text-indigo-100">Sign In</p>
        </div>

        <div className="bg-white rounded-xl shadow-2xl p-8">
          {message && (
            <div
              className={`mb-6 p-4 rounded-lg text-sm font-medium ${
                messageType === 'error'
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-green-50 text-green-700 border border-green-200'
              }`}
            >
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="subdomain" className="block text-sm font-medium text-gray-700 mb-1">
                Company Subdomain
              </label>
              <input
                id="subdomain"
                type="text"
                placeholder="e.g., acme-corp"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                value={subdomain}
                onChange={(e) => setSubdomain(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                placeholder="Your username"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Your password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Don't have an account? <a href="/" className="text-indigo-600 hover:text-indigo-700 font-medium">Sign up here</a>
          </div>
        </div>
      </div>
    </div>
  );
}
