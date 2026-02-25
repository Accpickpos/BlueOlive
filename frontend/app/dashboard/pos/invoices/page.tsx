"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, FileText, Eye, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/useAuth";
import { usePOSAPI } from "@/lib/posApi";

export default function InvoicesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    const fetchInvoices = async () => {
      if (authLoading || !user) return;
      
      try {
        setLoading(true);
        const response = await posAPI.listInvoices();
        
        // Transform API response to match frontend format
        const invoiceData = response.results || [];
        setInvoices(invoiceData.map((inv: any) => ({
          id: inv.invoice_number || inv.id,
          invoice_number: inv.invoice_number,
          client: inv.debtor_account_number || inv.debtor || 'Unknown',
          debtor_name: inv.debtor_name || inv.debtor?.name || '',
          amount: Number(inv.total_amount || inv.balance_due || 0),
          due: inv.due_date || inv.delivery_date || inv.invoice_date,
          status: inv.is_cancelled ? 'Cancelled' : inv.is_posted ? 'Paid' : 'Pending',
          invoice_date: inv.invoice_date,
          balance_due: Number(inv.balance_due || inv.total_amount || 0),
        })));
      } catch (error) {
        console.error('Error fetching invoices:', error);
        setInvoices([]);
      } finally {
        setLoading(false);
      }
    };

    fetchInvoices();
  }, [user, authLoading, posAPI]);

  const filteredInvoices =
    filter === "All" ? invoices : invoices.filter((inv) => inv.status === filter);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard/pos">
              <Button variant="ghost" size="icon" className="hover:bg-slate-200">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Invoices</h1>
              <p className="text-slate-600 mt-1">Manage customer invoices</p>
            </div>
          </div>
          <Link href="/dashboard/pos/invoices/create">
            <Button className="gap-2 bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4" />
              New Invoice
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          {["All", "Paid", "Pending", "Overdue"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg border transition ${
                filter === status 
                  ? "bg-blue-600 text-white border-blue-600" 
                  : "bg-white border-slate-300 hover:border-slate-400"
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Invoice Table */}
        <Card>
          <CardHeader>
            <CardTitle>Invoices ({filteredInvoices.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <p className="text-slate-600">Loading invoices...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-left border-b-2">
                      <th className="p-3">Invoice #</th>
                      <th className="p-3">Client</th>
                      <th className="p-3 text-right">Amount</th>
                      <th className="p-3">Due Date</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInvoices.map((invoice) => (
                      <tr key={invoice.id} className="border-b hover:bg-slate-50">
                        <td className="p-3 font-medium text-slate-900">{invoice.invoice_number || invoice.id}</td>
                        <td className="p-3 text-slate-600">{invoice.debtor_name || invoice.client}</td>
                        <td className="p-3 text-right font-semibold text-slate-900">R{Number(invoice.amount || 0).toFixed(2)}</td>
                        <td className="p-3 text-slate-600">{invoice.due}</td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium inline-block ${
                              invoice.status === "Paid"
                                ? "bg-green-100 text-green-700"
                                : invoice.status === "Pending"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {invoice.status}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Link href={`/dashboard/pos/invoices/${invoice.id}`}>
                            <Button size="sm" variant="ghost">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredInvoices.length === 0 && (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-600 font-medium mb-2">No invoices found</p>
                    <p className="text-slate-500 text-sm mb-4">Try adjusting your filters</p>
                    <Link href="/dashboard/pos/invoices/create">
                      <Button className="gap-2 bg-blue-600">
                        <Plus className="h-4 w-4" />
                        Create First Invoice
                      </Button>
                    </Link>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
