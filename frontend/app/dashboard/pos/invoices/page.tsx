"use client";
import { useState } from "react";
import Link from "next/link";
import { Plus, FileText, Eye, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const initialInvoices = [
  { id: "INV-001", client: "Acme Corp", amount: "$2,400", due: "2025-09-05", status: "Paid" },
  { id: "INV-002", client: "Globex", amount: "$1,800", due: "2025-09-10", status: "Pending" },
  { id: "INV-003", client: "Initech", amount: "$3,200", due: "2025-08-28", status: "Overdue" },
  { id: "INV-004", client: "Umbrella", amount: "$950", due: "2025-09-12", status: "Pending" },
];

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState(initialInvoices);
  const [filter, setFilter] = useState("All");

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
                      <td className="p-3 font-medium text-slate-900">{invoice.id}</td>
                      <td className="p-3 text-slate-600">{invoice.client}</td>
                      <td className="p-3 text-right font-semibold text-slate-900">{invoice.amount}</td>
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
