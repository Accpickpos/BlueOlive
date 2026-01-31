'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FileText, 
  CreditCard, 
  Receipt, 
  Package, 
  AlertCircle,
  TrendingUp,
  MoreVertical,
  ChevronRight
} from 'lucide-react';

export default function POSDashboard() {
  const { user, isLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get today's date range
        const today = new Date().toISOString().split('T')[0];
        const summary = await posAPI.getTransactionSummary({
          from_date: today,
          to_date: today,
        });
        
        setSummary(summary);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load summary');
      } finally {
        setLoading(false);
      }
    };

    if (user?.tenant?.slug) {
      fetchSummary();
    }
  }, [user?.tenant?.slug]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <p>Not authenticated</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const transactionCards = [
    {
      title: 'New Invoice',
      description: 'Create credit sale',
      href: '/dashboard/pos/invoices/create',
      icon: FileText,
      color: 'blue',
      count: summary?.invoice_count || 0,
    },
    {
      title: 'Cash Sale',
      description: 'Record cash transaction',
      href: '/dashboard/pos/cash-sales/create',
      icon: CreditCard,
      color: 'green',
      count: summary?.cash_sale_count || 0,
    },
    {
      title: 'Receipt',
      description: 'Record payment received',
      href: '/dashboard/pos/receipts/create',
      icon: Receipt,
      color: 'purple',
      count: summary?.receipt_count || 0,
    },
    {
      title: 'Laybye',
      description: 'Laybye payment plan',
      href: '/dashboard/pos/laybyes/create',
      icon: Package,
      color: 'orange',
      count: 0,
    },
  ];

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; border: string; hover: string }> = {
      blue: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200', hover: 'hover:border-blue-300 hover:shadow-md' },
      green: { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200', hover: 'hover:border-green-300 hover:shadow-md' },
      purple: { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200', hover: 'hover:border-purple-300 hover:shadow-md' },
      orange: { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-200', hover: 'hover:border-orange-300 hover:shadow-md' },
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 p-6 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Point of Sale</h1>
            <p className="text-slate-600 mt-2">
              Tenant: <span className="font-semibold text-slate-900">{user.tenant?.name}</span>
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <div className="text-right">
              <p className="text-xs text-slate-500 uppercase tracking-wide">Today</p>
              <p className="text-lg font-semibold text-slate-900">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
              </p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Quick Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {transactionCards.map((card) => {
            const Icon = card.icon;
            const colors = getColorClasses(card.color);
            return (
              <Link key={card.href} href={card.href}>
                <Card className={`h-full transition-all cursor-pointer border ${colors.border} ${colors.bg} ${colors.hover}`}>
                  <CardContent className="pt-6 pb-4">
                    <div className="flex items-start justify-between mb-4">
                      <div className={`p-3 rounded-lg bg-white ${colors.text}`}>
                        <Icon className="h-6 w-6" />
                      </div>
                      <span className="text-2xl font-bold text-slate-900">{card.count}</span>
                    </div>
                    <h3 className="font-semibold text-slate-900">{card.title}</h3>
                    <p className="text-sm text-slate-600 mt-1">{card.description}</p>
                    <div className="mt-4 flex items-center gap-2 text-sm font-medium text-slate-700 group">
                      <span>Get started</span>
                      <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Today's Summary */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Today's Summary</CardTitle>
                  <CardDescription>Transaction overview</CardDescription>
                </div>
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="h-8 w-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-slate-600 text-sm">Loading summary...</p>
                  </div>
                </div>
              ) : summary ? (
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-xs text-blue-600 font-medium uppercase tracking-wide">Invoices</p>
                    <p className="text-2xl font-bold text-slate-900 mt-2">{summary.invoice_count || 0}</p>
                    <p className="text-xs text-slate-600 mt-1">Credit sales</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-xs text-green-600 font-medium uppercase tracking-wide">Cash Sales</p>
                    <p className="text-2xl font-bold text-slate-900 mt-2">{summary.cash_sale_count || 0}</p>
                    <p className="text-xs text-slate-600 mt-1">Cash transactions</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <p className="text-xs text-purple-600 font-medium uppercase tracking-wide">Receipts</p>
                    <p className="text-2xl font-bold text-slate-900 mt-2">{summary.receipt_count || 0}</p>
                    <p className="text-xs text-slate-600 mt-1">Payments received</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-slate-500">No transactions recorded today</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Links */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Links</CardTitle>
              <CardDescription>View transactions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link href="/dashboard/pos/invoices">
                <Button variant="ghost" className="w-full justify-between text-left">
                  <span>All Invoices</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/dashboard/pos/cash-sales">
                <Button variant="ghost" className="w-full justify-between text-left">
                  <span>All Cash Sales</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/dashboard/pos/receipts">
                <Button variant="ghost" className="w-full justify-between text-left">
                  <span>All Receipts</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/dashboard/pos/reports">
                <Button variant="ghost" className="w-full justify-between text-left">
                  <span>Reports</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
