'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { login } from '@/lib/api';
import { useAuthContext } from '@/lib/AuthContext';
import { setTenant, setShops, setCurrentShop } from '@/lib/shopContext';
import { ArrowLeft, BarChart3 } from 'lucide-react';
import type { MaybeAxiosError } from '@/lib/types/errors';
import MultiStepSignupForm from '@/components/signup/MultiStepSignupForm';

export default function AuthPage() {
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  const { refetch } = useAuthContext();
  
  // Login form state
  const [loginData, setLoginData] = useState({
    subdomain: '',
    username: '',
    password: '',
  });

  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messageType, setMessageType] = useState<'error' | 'success'>('error');
  const router = useRouter();

  // Don't pre-fetch CSRF token - let it be fetched on-demand during login
  // Pre-fetching can trigger rate limiting on stale sessions

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    if (!loginData.subdomain || !loginData.username || !loginData.password) {
      setMessage('Please fill in all fields');
      setMessageType('error');
      setLoading(false);
      return;
    }

    try {
      const response = await login(loginData.subdomain, loginData.username, loginData.password);
      
      if (response.status === 200) {
        setMessage('Login successful! Redirecting...');
        setMessageType('success');
        
        // Store tenant in localStorage for API requests
        setTenant(loginData.subdomain);
        
        // Use the shop from the login response (already set by backend)
        const shop = response.data.shop;
        const shops = response.data.accessible_shops || [];
        
        setShops(shops);
        
        if (shop) {
          // Use the shop selected during login (or default set by backend)
          setCurrentShop(shop);
        } else if (shops.length > 0) {
          // Fallback to first shop if no shop in response
          setCurrentShop(shops[0]);
        }
        
        // Refetch user profile to update AuthContext
        await refetch();
        
        await new Promise(resolve => setTimeout(resolve, 500));
        router.push('/dashboard');
      }
    } catch (error: unknown) {
      const errorMsg = 
        (error as MaybeAxiosError)?.response?.data?.detail || 
        (error as MaybeAxiosError)?.message ||
        'Login failed. Please check your credentials.';
      setMessage(errorMsg);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 py-6 px-4 sm:px-6 lg:px-8">
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between mb-8 max-w-md mx-auto w-full">
        <Link 
          href="/" 
          className="flex items-center gap-2 text-white hover:text-indigo-100 transition font-semibold text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <Link 
          href="/" 
          className="flex items-center gap-2 text-white hover:text-indigo-100 transition"
        >
          <div className="bg-white rounded p-1">
            <BarChart3 className="h-4 w-4 text-indigo-600" />
          </div>
          <span className="font-bold text-lg">BlueOlive</span>
        </Link>
        <div className="w-12"></div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className={`w-full ${activeTab === 'signup' ? 'max-w-2xl' : 'max-w-md'}`}>
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-white rounded-full p-3 shadow-lg">
              <svg className="w-8 h-8 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.5 1.5H2a1 1 0 00-1 1v15a1 1 0 001 1h16a1 1 0 001-1v-9.5" />
              </svg>
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">BlueOlive</h1>
          <p className="text-indigo-100">Retail Management Made Simple</p>
        </div>

        {/* Tab Container */}
        <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('login')}
              className={`flex-1 py-3 px-4 font-medium text-sm transition-colors ${
                activeTab === 'login'
                  ? 'bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setActiveTab('signup')}
              className={`flex-1 py-3 px-4 font-medium text-sm transition-colors ${
                activeTab === 'signup'
                  ? 'bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form Container */}
          <div className={activeTab === 'signup' ? 'p-4 sm:p-6 bg-gray-950' : 'p-8'}>
            {/* Message */}
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

            {/* Login Form */}
            {activeTab === 'login' && (
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label htmlFor="login-subdomain" className="block text-sm font-medium text-gray-700 mb-1">
                    Company Subdomain
                  </label>
                  <input
                    id="login-subdomain"
                    type="text"
                    placeholder="e.g., acme-corp"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                    value={loginData.subdomain}
                    onChange={(e) => setLoginData({ ...loginData, subdomain: e.target.value })}
                  />
                  <p className="mt-1 text-xs text-gray-500">Your company&apos;s unique identifier</p>
                </div>

                <div>
                  <label htmlFor="login-username" className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <input
                    id="login-username"
                    type="text"
                    placeholder="Your username"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                    value={loginData.username}
                    onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                  />
                </div>

                <div>
                  <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    placeholder="Your password"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>

                <div className="text-center mt-4">
                  <Link 
                    href="/" 
                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Home
                  </Link>
                </div>
              </form>
            )}

            {/* Signup Form */}
            {activeTab === 'signup' && <MultiStepSignupForm />}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-indigo-100 text-sm">
            A modern solution for managing your retail business
          </p>
        </div>
        </div>
      </div>
    </div>
  );
}
