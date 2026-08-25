"use client";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { useAuth } from "@/lib/useAuth";
import { usePOSAPI } from "@/lib/posApi";

interface Quote {
  id: number;
  number: string;
  customer: string;
  amount: number;
  expiry: string;
  status: string;
}

export default function QuotesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);

  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchQuotes = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listQuotations();
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setQuotes(
          raw.map((q: any) => ({
            id: q.id,
            number: q.quotation_number ?? String(q.id),
            customer: q.customer_name ?? "Unknown",
            amount: Number(q.total_amount ?? 0),
            expiry: q.expiry_date ?? "",
            status: String(q.status ?? "ACTIVE").toLowerCase(),
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error("Error fetching quotes:", error);
          setQuotes([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchQuotes();
    return () => { cancelled = true; };
  }, [user, authLoading]);

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
                          quote.status === "converted_to_invoice" || quote.status === "invoiced" || quote.status === "job" ? "bg-green-100 text-green-800" :
                          quote.status === "cancelled" || quote.status === "expired" ? "bg-gray-100 text-gray-800" :
                          "bg-blue-100 text-blue-800"
                        }`}>
                          {quote.status.replace(/_/g, " ")}
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