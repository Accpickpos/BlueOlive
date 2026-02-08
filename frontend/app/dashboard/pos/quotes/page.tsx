"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";

interface Quote {
  id: number;
  number: string;
  customer: string;
  amount: number;
  expiry: string;
  status: string;
}

export default function QuotesPage() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchQuotes();
  }, []);

  const fetchQuotes = async () => {
    setLoading(true);
    try {
      setTimeout(() => {
        setQuotes([
          { id: 1, number: "QT-001", customer: "John Smith", amount: 3500.00, expiry: "2025-03-15", status: "sent" },
          { id: 2, number: "QT-002", customer: "ABC Corp", amount: 5000.00, expiry: "2025-03-20", status: "accepted" },
          { id: 3, number: "QT-003", customer: "Tech Solutions", amount: 2200.00, expiry: "2025-02-28", status: "draft" },
        ]);
      }, 300);
    } catch (error) {
      console.error("Error fetching quotes:", error);
    } finally {
      setTimeout(() => setLoading(false), 400);
    }
  };

  const filteredQuotes = quotes.filter((quote) =>
    quote.number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    quote.customer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Quotations</h1>
        <Link href="/dashboard/pos/quotes/create">
          <Button className="bg-blue-600 hover:bg-blue-700">New Quote</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Customer Quotes</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            type="text"
            placeholder="Search by quote number or customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-4"
          />
          {filteredQuotes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Quote #</th>
                    <th className="text-left py-2">Customer</th>
                    <th className="text-right py-2">Amount</th>
                    <th className="text-left py-2">Expiry Date</th>
                    <th className="text-left py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQuotes.map((quote) => (
                    <tr key={quote.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{quote.number}</td>
                      <td className="py-3">{quote.customer}</td>
                      <td className="py-3 text-right">R{quote.amount.toFixed(2)}</td>
                      <td className="py-3">{quote.expiry}</td>
                      <td className="py-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          quote.status === "accepted" ? "bg-green-100 text-green-800" :
                          quote.status === "draft" ? "bg-gray-100 text-gray-800" :
                          "bg-blue-100 text-blue-800"
                        }`}>
                          {quote.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">No quotes found</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}